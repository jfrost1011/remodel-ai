import os
from typing import Optional, List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
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
        
        # Session data cache
        self.session_data_cache = {}
        
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
            
            # Create retrieval chain
            self.qa_chain = self._create_qa_chain()
            print("Pinecone vector store initialized successfully")
                
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {str(e)}")
            self.vector_store = None
            self.qa_chain = None
    
    def _create_qa_chain(self):
        """Create a retrieval QA chain with custom prompt"""
        prompt_template = """You are an expert AI construction cost advisor specializing in California residential construction.
        
Context: {context}

Question: {question}

Instructions:
- Provide accurate cost estimates and timelines based on the context
- Focus only on the specific location mentioned (San Diego or Los Angeles)
- Include both cost ranges and timeline information
- Be conversational but professional
- If the costs seem low, mention these may be budget-level options
- For quality questions, explain what different price points typically mean

Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 5}
            ),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
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
    
    def extract_context_from_history(self, query: str, chat_history: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Extract context from conversation history"""
        context = {
            'location': None,
            'project_type': None,
            'is_quality_question': False,
            'is_followup': False
        }
        
        query_lower = query.lower()
        
        # Check if this is a quality-related question
        quality_keywords = ['high end', 'low end', 'mid range', 'luxury', 'standard', 'basic', 'quality', 'that for', 'economy']
        context['is_quality_question'] = any(keyword in query_lower for keyword in quality_keywords)
        
        # Extract from current query
        if 'san diego' in query_lower:
            context['location'] = 'San Diego'
        elif 'los angeles' in query_lower or ' la ' in query_lower:
            context['location'] = 'Los Angeles'
        
        project_types = {
            'kitchen': ['kitchen'],
            'bathroom': ['bathroom', 'bath'],
            'room_addition': ['room addition', 'addition'],
            'adu': ['adu', 'accessory dwelling'],
            'garage': ['garage']
        }
        
        for ptype, keywords in project_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    context['project_type'] = ptype
                    break
        
        # If not found in current query, check history
        if not context['location'] or not context['project_type']:
            context['is_followup'] = True
            # Look through history from most recent to oldest
            for human, ai in reversed(chat_history[-3:]):
                human_lower = human.lower()
                ai_lower = ai.lower()
            
                if not context['location']:
                    if 'san diego' in human_lower or 'san diego' in ai_lower:
                        context['location'] = 'San Diego'
                    elif 'los angeles' in human_lower or 'los angeles' in ai_lower:
                        context['location'] = 'Los Angeles'
            
                if not context['project_type']:
                    for ptype, keywords in project_types.items():
                        for keyword in keywords:
                            if keyword in human_lower or keyword in ai_lower:
                                context['project_type'] = ptype
                                break
            
                if context['location'] and context['project_type']:
                    break
        
        return context

    async def get_chat_response(self, query: str, chat_history: List[Tuple[str, str]], session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get response from the RAG system"""
        logger.info(f"Getting chat response for query: {query}")
        
        # Handle non-construction queries
        if not self.is_construction_query(query):
            prompt = f"""You are a friendly AI assistant for a construction cost estimation service.
The user said: "{query}"

If they're greeting you or having general conversation, respond naturally and briefly mention that you can help with construction/remodeling cost estimates for San Diego and Los Angeles.
Keep your response conversational and brief."""
            
            response = await self.llm.ainvoke(prompt)
            return {
                "message": response.content,
                "source_documents": []
            }
        
        if not self.qa_chain:
            return {
                "message": "I'm sorry, but I'm having trouble accessing the construction database. Please check back later.",
                "source_documents": []
            }
        
        try:
            # Extract context from conversation
            context = self.extract_context_from_history(query, chat_history)
            logger.info(f"Extracted context: {context}")
            
            # Get or create session cache
            if session_id and session_id not in self.session_data_cache:
                self.session_data_cache[session_id] = {}
            
            session_cache = self.session_data_cache.get(session_id, {}) if session_id else {}
            
            # Enhance query with context if available
            enhanced_query = query
            if context['location'] and context['project_type']:
                enhanced_query = f"{context['project_type']} remodel in {context['location']}: {query}"
            elif context['location']:
                enhanced_query = f"In {context['location']}: {query}"
            elif context['project_type']:
                enhanced_query = f"{context['project_type']} remodel: {query}"
            
            # Use LangChain's QA chain
            result = await self.qa_chain.ainvoke({"query": enhanced_query})
            
            # Cache the results if we have complete context
            if context['location'] and context['project_type']:
                cache_key = f"{context['location']}_{context['project_type']}"
                session_cache[cache_key] = {
                    'response': result['result'],
                    'source_documents': result.get('source_documents', [])
                }
                if session_id:
                    self.session_data_cache[session_id] = session_cache
            
            return {
                "message": result['result'],
                "source_documents": result.get('source_documents', [])
            }
            
        except Exception as e:
            logger.error(f"Error in get_chat_response: {str(e)}", exc_info=True)
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "source_documents": []
            }