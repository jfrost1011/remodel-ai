import os
import uuid
from typing import Optional, List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import Document
from pinecone import Pinecone as PineconeClient
from config import settings
import logging
import json
import re

logger = logging.getLogger(__name__)
from services.context_manager import ContextManager, ConversationContext
from services.city_mappings import normalize_location, CITY_MAPPINGS

class RAGService:
    def __init__(self):
        print("Initializing RAG Service...")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.3
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model
        )
        
        # Session storage for memory and context
        self.context_manager = ContextManager()
        # Store non-serializable objects separately
        self.sessions = {}  # Store qa_chain and memory objects
        
        # Define minimum realistic costs for each project type
        self.min_realistic_costs = {
            'kitchen': 25000,
            'bathroom': 10000,
            'room_addition': 50000,
            'adu': 80000,
            'garage': 20000,
            'landscaping': 5000
        }
        
        # Initialize Pinecone with LangChain
        try:
            pc = PineconeClient(api_key=settings.pinecone_api_key)
            
            # Initialize LangChain's Pinecone vector store
            self.vector_store = PineconeVectorStore(
                index_name=settings.pinecone_index,
                embedding=self.embeddings,
                pinecone_api_key=settings.pinecone_api_key
            )
            
            print("Pinecone vector store initialized successfully")
                
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {str(e)}")
            self.vector_store = None
    
    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create a session with memory and context"""
        context = self.context_manager.get_or_create_context(session_id)
        # Check if this is a new session
        # Check if this is a new session
        session_key = f'session_{session_id}'
        if session_key not in self.sessions:
            # Create memory for this session
            memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=500,
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            # Create QA chain for this session
            qa_chain = self._create_qa_chain(memory)
            # Update metadata with chain and memory
            # Store non-serializable objects in sessions dict
            session_key = f'session_{session_id}'
            self.sessions[session_key] = {
                'qa_chain': qa_chain,
                'memory': memory
            }
            # Save context
            self.context_manager.save_context(session_id, context)
        return {
            'memory': self.sessions.get(f'session_{session_id}', {}).get('memory'),
            'context': context,
            'qa_chain': self.sessions.get(f'session_{session_id}', {}).get('qa_chain')
            'conversation_summary': context.conversation_summary
        }
    
    def _create_qa_chain(self, memory):
        """Create a conversational retrieval chain with memory"""
        # System prompt that strongly emphasizes context preservation
        system_template = """You are an expert AI construction cost advisor specializing in California residential construction, particularly in San Diego and Los Angeles.

        CRITICAL INSTRUCTIONS:
        1. ALWAYS maintain the context of the conversation. If discussing a specific project type (like kitchen remodel), continue with that context unless the user explicitly changes topics.
        2. Reference specific numbers and details you've already provided in the conversation.
        3. When asked follow-up questions, directly refer to your previous answers.
        4. Stay focused on the specific project type being discussed.
        5. If the user asks about timelines after discussing a kitchen remodel, give the kitchen remodel timeline, not general construction timelines.
        6. Remember and use the exact price ranges you've mentioned earlier in the conversation.
        
        Previous conversation summary: {chat_history}
        
        Context from search: {context}
        
        Human: {question}
        
        Assistant: I'll respond based on our ongoing conversation about your specific project."""
        
        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
        
        CHAT_PROMPT = ChatPromptTemplate.from_messages(messages)
        
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
            memory=memory,
            combine_docs_chain_kwargs={
                "prompt": CHAT_PROMPT,
                "document_separator": "\n"
            },
            return_source_documents=True,
            verbose=False
        )
    
    def is_construction_query(self, query: str) -> bool:
        """Determine if the query is about construction/remodeling"""
        # If we have an active session, assume follow-ups are construction-related
        construction_keywords = [
            'cost', 'price', 'estimate', 'remodel', 'renovation', 'kitchen', 'bathroom',
            'project', 'construction', 'timeline', 'budget', 'appliances', 'materials',
            'san diego', 'los angeles', 'proceed', 'first step', 'summarize'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in construction_keywords)
    
    def update_session_context(self, query: str, response: str, session_id: str):
        """Update session context based on query and response"""
        context = self.context_manager.get_or_create_context(session_id)
        query_lower = query.lower()
        response_lower = response.lower()
        updates = {}
        # Extract location
        # Extract location using city mappings
        query_location = normalize_location(query_lower)
        response_location = normalize_location(response_lower)
        # Check if user is explicitly changing location
        if "instead" in query_lower or "what about" in query_lower or "switch to" in query_lower:
            if query_location:
                updates['location'] = query_location
        elif query_location:
            updates['location'] = query_location
        elif response_location and not context.location:
            updates['location'] = response_location
        # Extract project type
        project_types = {
            'kitchen': ['kitchen'],
            'bathroom': ['bathroom', 'bath'],
            'room_addition': ['room addition', 'addition'],
            'adu': ['adu', 'accessory dwelling'],
            'garage': ['garage']
        }
        for ptype, keywords in project_types.items():
            for keyword in keywords:
                if keyword in query_lower or keyword in response_lower:
                    updates['project_type'] = ptype
                    break
        # Extract price information from response
        price_pattern = r'\$(\d{1,3}(?:,\d{3})*)'
        prices = re.findall(price_pattern, response)
        if prices and context.project_type:
            if not context.discussed_prices:
                context.discussed_prices = {}
            context.discussed_prices[context.project_type] = prices
            updates['discussed_prices'] = context.discussed_prices
        # Extract timeline information
        timeline_pattern = r'(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?'
        timeline_match = re.search(timeline_pattern, response_lower)
        if timeline_match:
            updates['timeline'] = f"{timeline_match.group(1)}-{timeline_match.group(2)} weeks"
        # Update conversation summary
        summary = f"Discussing {context.project_type or 'construction'} project in {context.location or 'California'}. Budget discussed: {context.discussed_prices or {}}. Timeline: {context.timeline or 'Not discussed'}."
        updates['conversation_summary'] = summary
        # Calculate budget range from discussed prices
        if context.discussed_prices and context.project_type:
            project_prices = context.discussed_prices.get(context.project_type, [])
            if project_prices:
                numeric_prices = []
                for price in project_prices:
                    try:
                        numeric_price = int(price.replace(',', ''))
                        numeric_prices.append(numeric_price)
                    except:
                        continue
                if numeric_prices:
                    updates['budget_range'] = {
                        "min": min(numeric_prices),
                        "max": max(numeric_prices)
                    }
        # Update context with all changes
        # Get the context
        context = self.context_manager.get_or_create_context(session_id)
        # Apply updates
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
        # Save the updated context
        self.context_manager.save_context(session_id, context)
    async def _validate_and_correct_response(self, response_text: str, session_id: str) -> str:
        """Validate response consistency with known context and correct if needed"""
        context = self.context_manager.get_or_create_context(session_id)
        # Check for price consistency
        if context.discussed_prices and context.project_type:
            known_prices = context.discussed_prices.get(context.project_type, [])
            if known_prices:
                # Extract prices from response
                response_prices = re.findall(r'\$(\d{1,3}(?:,\d{3})*)', response_text)
                if response_prices and known_prices:
                    # Check if response prices differ significantly from known prices
                    response_min = min(int(p.replace(',', '')) for p in response_prices)
                    response_max = max(int(p.replace(',', '')) for p in response_prices)
                    known_min = min(int(p.replace(',', '')) for p in known_prices)
                    known_max = max(int(p.replace(',', '')) for p in known_prices)
                    # If there's a significant discrepancy, correct it
                    if abs(response_min - known_min) > 5000 or abs(response_max - known_max) > 10000:
                        correction_prompt = f"""
                        The response appears inconsistent with our established budget range of 
                        ${known_min:,} to ${known_max:,} for this {context.project_type} remodel. 
                        Original response: {response_text}
                        Please provide a corrected response that maintains consistency with the previously 
                        discussed budget range while answering the user's question.
                        """
                        corrected = await self.llm.ainvoke(correction_prompt)
                        return corrected.content
        # Check for timeline consistency
        if context.timeline:
            # Extract timeline from response
            timeline_pattern = r'(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?'
            response_timeline = re.search(timeline_pattern, response_text)
            if response_timeline and context.timeline != f"{response_timeline.group(1)}-{response_timeline.group(2)} weeks":
                correction_prompt = f"""
                The response timeline appears inconsistent with our established timeline of {context.timeline}. 
                Original response: {response_text}
                Please provide a corrected response that maintains consistency with the previously 
                discussed timeline while answering the user's question.
                """
                corrected = await self.llm.ainvoke(correction_prompt)
                return corrected.content
        return response_text

    async def get_chat_response(self, query: str, chat_history: List[Tuple[str, str]], session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get response from the RAG system"""
        logger.info(f"Getting chat response for query: {query}")
        
        # Ensure we have a session ID
        if not session_id:
            session_id = str(uuid.uuid4())
        logger.info(f"Using session ID: {session_id}")
        
        # Get or create session
        session = self.get_or_create_session(session_id)
        
        # Handle greetings but keep session active
        if not self.is_construction_query(query) and not session['context'].project_type:
            prompt = f"""You are a friendly AI assistant for a construction cost estimation service.
The user said: "{query}"

Respond naturally and mention that you can help with construction/remodeling cost estimates for San Diego and Los Angeles.
Keep your response conversational and brief."""
            
            response = await self.llm.ainvoke(prompt)
            return {
                "message": response.content,
                "source_documents": []
            }
        
        if not self.vector_store:
            return {
                "message": "I'm sorry, but I'm having trouble accessing the construction database. Please check back later.",
                "source_documents": []
            }
        
        try:
            # Use the session's QA chain
            qa_chain = session['qa_chain']
            
            # Create an enhanced query that includes critical context
            context = session['context']
            enhanced_query = query
            
            # Add context to maintain conversation continuity
            if context.project_type and 'kitchen' not in query.lower() and 'bathroom' not in query.lower():
                enhanced_query = f"Regarding the {context.project_type} remodel we're discussing: {query}"
            
            # Include location context if relevant
            if context.location and context.location.lower() not in query.lower():
                enhanced_query = f"In {context.location}, {enhanced_query}"
            
            logger.info(f"Enhanced query: {enhanced_query}")
            
            # Get response from chain
            result = await qa_chain.ainvoke({"question": enhanced_query})
            
            response_text = result.get('answer', '')
            
            # Validate and correct response if needed
            response_text = await self._validate_and_correct_response(response_text, session_id)
            # Update session context with this exchange
            self.update_session_context(query, response_text, session_id)
            
            # Log the updated context
            logger.info(f"Updated context: {session['context'].to_dict()}")
            
            return {
                "message": response_text,
                "source_documents": result.get('source_documents', []),
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in get_chat_response: {str(e)}", exc_info=True)
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "source_documents": []
            }
