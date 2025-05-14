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

logger = logging.getLogger(__name__)

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
        self.sessions = {}
        
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
        if session_id not in self.sessions:
            # Create memory for this session
            memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=500,
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            
            # Create context tracking
            context = {
                'location': None,
                'project_type': None,
                'budget_range': None,
                'timeline': None,
                'discussed_prices': {},
                'specific_features': []
            }
            
            # Create QA chain for this session
            qa_chain = self._create_qa_chain(memory)
            
            self.sessions[session_id] = {
                'memory': memory,
                'context': context,
                'qa_chain': qa_chain,
                'conversation_summary': ""
            }
        
        return self.sessions[session_id]
    
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
    
    def update_session_context(self, query: str, response: str, session: Dict[str, Any]):
        """Update session context based on query and response"""
        context = session['context']
        query_lower = query.lower()
        response_lower = response.lower()
        
        # Extract location
        if 'san diego' in query_lower or 'san diego' in response_lower:
            context['location'] = 'San Diego'
        elif 'los angeles' in query_lower or 'los angeles' in response_lower:
            context['location'] = 'Los Angeles'
        
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
                    context['project_type'] = ptype
                    break
        
        # Extract price information from response
        import re
        price_pattern = r'\$(\d{1,3}(?:,\d{3})*)'
        prices = re.findall(price_pattern, response)
        if prices and context.get('project_type'):
            context['discussed_prices'][context['project_type']] = prices
        
        # Extract timeline information
        timeline_pattern = r'(\d+)\s*(?:to|-)\s*(\d+)\s*weeks?'
        timeline_match = re.search(timeline_pattern, response_lower)
        if timeline_match:
            context['timeline'] = f"{timeline_match.group(1)}-{timeline_match.group(2)} weeks"
        
        # Update conversation summary
        session['conversation_summary'] = f"Discussing {context.get('project_type', 'construction')} project in {context.get('location', 'California')}. Budget discussed: {context.get('discussed_prices', {})}. Timeline: {context.get('timeline', 'Not discussed')}."

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
        if not self.is_construction_query(query) and not session['context']['project_type']:
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
            if context['project_type'] and 'kitchen' not in query.lower() and 'bathroom' not in query.lower():
                enhanced_query = f"Regarding the {context['project_type']} remodel we're discussing: {query}"
            
            # Include location context if relevant
            if context['location'] and context['location'].lower() not in query.lower():
                enhanced_query = f"In {context['location']}, {enhanced_query}"
            
            logger.info(f"Enhanced query: {enhanced_query}")
            
            # Get response from chain
            result = await qa_chain.ainvoke({"question": enhanced_query})
            
            response_text = result.get('answer', '')
            
            # Update session context with this exchange
            self.update_session_context(query, response_text, session)
            
            # Log the updated context
            logger.info(f"Updated context: {session['context']}")
            
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