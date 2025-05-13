import os
from typing import Optional, List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from pinecone import Pinecone as PineconeClient
import openai
from config import settings

class RAGService:
    def __init__(self):
        print("Initializing RAG Service...")
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.3  # Lower temperature for more consistent responses
        )
        
        # Initialize OpenAI client directly
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Session data cache - stores data per session
        self.session_data_cache = {}
        
        # Initialize Pinecone
        try:
            pc = PineconeClient(api_key=settings.pinecone_api_key)
            indexes = pc.list_indexes()
            index_names = [idx.name for idx in indexes.indexes] if hasattr(indexes, 'indexes') else [idx.name for idx in indexes]
            
            if settings.pinecone_index not in index_names:
                print(f"Warning: Pinecone index '{settings.pinecone_index}' not found.")
                self.index = None
            else:
                self.index = pc.Index(settings.pinecone_index)
                print("Pinecone index initialized successfully")
                
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {str(e)}")
            self.index = None
    
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
            'is_quality_question': False
        }
        
        query_lower = query.lower()
        
        # Check if this is a quality-related question
        quality_keywords = ['high end', 'low end', 'mid range', 'luxury', 'standard', 'basic', 'quality', 'that for']
        context['is_quality_question'] = any(keyword in query_lower for keyword in quality_keywords)
        
        # Extract from current query
        if 'san diego' in query_lower:
            context['location'] = 'San Diego'
        elif 'los angeles' in query_lower or ' la ' in query_lower:
            context['location'] = 'Los Angeles'
        
        project_types = {
            'kitchen': ['kitchen'],
            'bathroom': ['bathroom', 'bath'],
            'room addition': ['room addition', 'addition'],
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
            # Look through history from most recent to oldest
            for human, ai in reversed(chat_history):
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
        print(f"Getting chat response for query: {query}")
        
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
        
        if not self.index:
            return {
                "message": "I'm sorry, but I'm having trouble accessing the construction database. Please check back later.",
                "source_documents": []
            }
        
        try:
            # Extract context from conversation
            context = self.extract_context_from_history(query, chat_history)
            print(f"Extracted context: {context}")
            
            # Get or create session cache
            if session_id and session_id not in self.session_data_cache:
                self.session_data_cache[session_id] = {}
            
            session_cache = self.session_data_cache.get(session_id, {}) if session_id else {}
            
            # Create cache key based on location and project type
            cache_key = f"{context.get('location', 'unknown')}_{context.get('project_type', 'unknown')}"
            
            # If this is a quality question about cached data, use the cached data
            if context['is_quality_question'] and cache_key in session_cache:
                cached_data = session_cache[cache_key]
                print(f"Using cached data for quality question: {cache_key}")
                
                prompt = f"""You are a construction cost advisor. The user previously asked about {cached_data['project_type']} remodel in {cached_data['location']}.

You provided these costs:
- Cost range: ${cached_data['cost_low']:,.0f} to ${cached_data['cost_high']:,.0f}
- Average: ${cached_data['cost_average']:,.0f}
- Timeline: {cached_data['timeline']} weeks

Current question: {query}

Answer their question about quality levels. Be consistent with the numbers you already provided.
Explain whether these costs represent high-end, mid-range, or budget options.
Do NOT provide different numbers or mention other locations."""
                
                response = await self.llm.ainvoke(prompt)
                return {
                    "message": response.content,
                    "source_documents": cached_data.get('source_documents', [])
                }
            
            # If we have cached data for this location/project, use it
            if cache_key in session_cache and not context['is_quality_question']:
                cached_data = session_cache[cache_key]
                print(f"Using cached data for: {cache_key}")
                
                prompt = f"""You are a construction cost advisor. Use this EXACT data to answer the question:

{cached_data['project_type']} remodel in {cached_data['location']}:
- Cost range: ${cached_data['cost_low']:,.0f} to ${cached_data['cost_high']:,.0f}
- Average: ${cached_data['cost_average']:,.0f}
- Timeline: {cached_data['timeline']} weeks

Question: {query}

Use these exact numbers in your response. Be helpful and conversational."""
                
                response = await self.llm.ainvoke(prompt)
                return {
                    "message": response.content,
                    "source_documents": cached_data.get('source_documents', [])
                }
            
            # Need to search for new data
            if not context['location'] or not context['project_type']:
                return {
                    "message": "I need more information to provide an accurate estimate. What type of project are you interested in, and in which city (San Diego or Los Angeles)?",
                    "source_documents": []
                }
            
            # Build search query
            search_query = f"{context['project_type']} remodel {context['location']} cost estimate"
            
            # Create embedding
            print(f"Creating embedding for: {search_query}")
            embedding_response = self.openai_client.embeddings.create(
                input=search_query,
                model=settings.embedding_model
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Search Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=10,
                include_metadata=True,
                namespace=""
            )
            
            # Filter for exact location and project type matches
            exact_matches = []
            for match in search_results.matches:
                if match.metadata:
                    meta_location = match.metadata.get('location', '')
                    meta_project = match.metadata.get('remodel_type', '').lower()
                    
                    if meta_location == context['location']:
                        if context['project_type'].replace(' ', '_') in meta_project or context['project_type'] in meta_project:
                            exact_matches.append(match)
            
            if not exact_matches:
                # Fallback to location-only matches
                for match in search_results.matches:
                    if match.metadata and match.metadata.get('location', '') == context['location']:
                        exact_matches.append(match)
            
            if not exact_matches:
                return {
                    "message": f"I don't have specific data for {context['project_type']} remodels in {context['location']}. Would you like estimates for other types of projects in that area?",
                    "source_documents": []
                }
            
            # Use the best match
            best_match = exact_matches[0]
            meta = best_match.metadata
            
            # Cache this data for the session
            if session_id:
                session_cache[cache_key] = {
                    'project_type': context['project_type'],
                    'location': context['location'],
                    'cost_low': meta.get('cost_low', 0),
                    'cost_high': meta.get('cost_high', 0),
                    'cost_average': meta.get('cost_average', 0),
                    'timeline': meta.get('timeline', 'Unknown'),
                    'source_documents': [meta]
                }
                self.session_data_cache[session_id] = session_cache
            
            # Create response
            prompt = f"""You are a construction cost advisor. Provide information about this project:

{context['project_type']} remodel in {context['location']}:
- Cost range: ${meta.get('cost_low', 0):,.0f} to ${meta.get('cost_high', 0):,.0f}
- Average cost: ${meta.get('cost_average', 0):,.0f}
- Timeline: {meta.get('timeline', 'Unknown')} weeks

Question: {query}

Provide a helpful, conversational response that includes both cost and timeline information.
Focus only on {context['location']} - do not mention other cities."""
            
            response = await self.llm.ainvoke(prompt)
            
            return {
                "message": response.content,
                "source_documents": [meta]
            }
            
        except Exception as e:
            print(f"Error in get_chat_response: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "source_documents": []
            }