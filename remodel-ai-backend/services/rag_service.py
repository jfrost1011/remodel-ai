import os
import uuid
from typing import Optional, List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from pinecone import Pinecone as PineconeClient
from config import settings
import logging

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
        
        # Session memory storage
        self.session_memory = {}
        
        # Session context tracking
        self.session_context = {}
        
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
    
    def get_or_create_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for a session"""
        if session_id not in self.session_memory:
            self.session_memory[session_id] = ConversationBufferWindowMemory(
                k=5,  # Keep last 5 exchanges
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
        return self.session_memory[session_id]
    
    def get_or_create_context(self, session_id: str) -> Dict[str, Any]:
        """Get or create context tracking for a session"""
        if session_id not in self.session_context:
            self.session_context[session_id] = {
                'location': None,
                'project_type': None,
                'last_discussed_project': None,
                'last_cost_range': None,
                'last_timeline': None
            }
        return self.session_context[session_id]
    
    def create_qa_chain(self, session_id: str):
        """Create a conversational retrieval chain with memory"""
        memory = self.get_or_create_memory(session_id)
        
        # Custom prompt that emphasizes context preservation
        prompt_template = """You are an expert AI construction cost advisor specializing in California residential construction.

        Current conversation context:
        {chat_history}

        Context from search:
        {context}

        Current question: {question}

        IMPORTANT INSTRUCTIONS:
        1. ALWAYS maintain the context of the conversation. If we were discussing a specific project type, continue discussing that unless the user explicitly changes topics.
        2. If the user asks follow-up questions, refer to the previous information you provided.
        3. Be consistent with any numbers, timelines, or estimates you've already given.
        4. For San Diego and Los Angeles, focus only on the location already being discussed.
        5. If uncertain about context, ask for clarification rather than changing topics.

        Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["chat_history", "context", "question"]
        )
        
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
            memory=memory,
            combine_docs_chain_kwargs={"prompt": PROMPT},
            return_source_documents=True,
            verbose=True
        )
    
    def is_construction_query(self, query: str) -> bool:
        """Determine if the query is about construction/remodeling"""
        construction_keywords = [
            'cost', 'price', 'estimate', 'remodel', 'renovation', 'kitchen', 'bathroom',
            'room', 'addition', 'adu', 'garage', 'conversion', 'flooring', 'roofing',
            'landscaping', 'pool', 'deck', 'patio', 'how much', 'budget', 'quote',
            'san diego', 'los angeles', 'la', 'california', 'timeline', 'duration',
            'project', 'construction', 'contractor', 'materials', 'labor', 'permit',
            'average', 'typical', 'usually', 'timeframe', 'long', 'weeks', 'months',
            'high end', 'low end', 'mid range', 'luxury', 'standard', 'basic', 'quality'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in construction_keywords)
    
    def extract_and_update_context(self, query: str, session_id: str) -> Dict[str, Any]:
        """Extract context from query and update session context"""
        context = self.get_or_create_context(session_id)
        query_lower = query.lower()
        
        # Check for location mentions
        if 'san diego' in query_lower:
            context['location'] = 'San Diego'
        elif 'los angeles' in query_lower or ' la ' in query_lower:
            context['location'] = 'Los Angeles'
        
        # Check for project type mentions
        project_types = {
            'kitchen': ['kitchen'],
            'bathroom': ['bathroom', 'bath'],
            'room_addition': ['room addition', 'addition'],
            'adu': ['adu', 'accessory dwelling'],
            'garage': ['garage'],
            'landscaping': ['landscaping', 'landscape']
        }
        
        for ptype, keywords in project_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    context['project_type'] = ptype
                    context['last_discussed_project'] = ptype
                    break
        
        # Check for cost level mentions
        if 'budget' in query_lower or 'low end' in query_lower:
            context['last_cost_range'] = 'budget'
        elif 'mid range' in query_lower or 'middle' in query_lower:
            context['last_cost_range'] = 'mid-range'
        elif 'high end' in query_lower or 'luxury' in query_lower:
            context['last_cost_range'] = 'high-end'
        
        return context

    async def get_chat_response(self, query: str, chat_history: List[Tuple[str, str]], session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get response from the RAG system"""
        logger.info(f"Getting chat response for query: {query}")
        logger.info(f"Session ID: {session_id}")
        
        # Handle non-construction queries
        if not self.is_construction_query(query) and not session_id:
            prompt = f"""You are a friendly AI assistant for a construction cost estimation service.
The user said: "{query}"

If they're greeting you or having general conversation, respond naturally and briefly mention that you can help with construction/remodeling cost estimates for San Diego and Los Angeles.
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
        
        # Ensure we have a session ID
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            # Extract and update context
            context = self.extract_and_update_context(query, session_id)
            logger.info(f"Current context: {context}")
            
            # Create or get the conversational chain for this session
            qa_chain = self.create_qa_chain(session_id)
            
            # Enhance query with context only if we're missing information
            enhanced_query = query
            if context.get('last_discussed_project') and 'kitchen' not in query.lower() and 'bathroom' not in query.lower():
                # If we have a previously discussed project and the current query doesn't mention a specific project
                enhanced_query = f"Regarding the {context['last_discussed_project']} remodel we were discussing: {query}"
            
            logger.info(f"Enhanced query: {enhanced_query}")
            
            # Use the conversational chain
            result = await qa_chain.ainvoke({"question": enhanced_query})
            
            # Extract timeline and cost info from response for context tracking
            response_text = result.get('answer', '')
            if 'weeks' in response_text.lower():
                import re
                weeks_match = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)\s*weeks', response_text.lower())
                if weeks_match:
                    context['last_timeline'] = f"{weeks_match.group(1)}-{weeks_match.group(2)} weeks"
            
            return {
                "message": response_text,
                "source_documents": result.get('source_documents', [])
            }
            
        except Exception as e:
            logger.error(f"Error in get_chat_response: {str(e)}", exc_info=True)
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "source_documents": []
            }
