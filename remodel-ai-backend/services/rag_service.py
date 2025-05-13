import os
from typing import Optional, List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from pinecone import Pinecone as PineconeClient
import openai
from config import settings
import json

class RAGService:
    def __init__(self):
        print("Initializing RAG Service...")
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.7
        )
        
        # Initialize OpenAI client directly
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Session data cache
        self.session_cache = {}
        
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
            'high end', 'low end', 'mid range', 'luxury', 'standard', 'basic'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in construction_keywords)
    
    def get_session_key(self, location: str, project_type: str) -> str:
        """Create a consistent key for caching session data"""
        return f"{location}_{project_type}".lower().replace(' ', '_')

    async def get_chat_response(self, query: str, chat_history: List[Tuple[str, str]]) -> Dict[str, Any]:
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
            location = None
            project_type = None
            
            # Check current query
            query_lower = query.lower()
            if 'san diego' in query_lower:
                location = 'San Diego'
            elif 'los angeles' in query_lower or ' la ' in query_lower:
                location = 'Los Angeles'
            
            project_types = ['kitchen', 'bathroom', 'room addition', 'adu', 'garage', 'landscaping']
            for pt in project_types:
                if pt in query_lower:
                    project_type = pt
                    break
            
            # If not in current query, check chat history
            if not location or not project_type:
                full_conversation = []
                for human, ai in chat_history:
                    full_conversation.append(human.lower())
                    full_conversation.append(ai.lower())
                
                conversation_text = " ".join(full_conversation)
                
                if not location:
                    if 'san diego' in conversation_text:
                        location = 'San Diego'
                    elif 'los angeles' in conversation_text or ' la ' in conversation_text:
                        location = 'Los Angeles'
                
                if not project_type:
                    for pt in project_types:
                        if pt in conversation_text:
                            project_type = pt
                            break
            
            print(f"Context - Location: {location}, Project Type: {project_type}")
            
            # Check if we have cached data for this location/project
            session_key = None
            if location and project_type:
                session_key = self.get_session_key(location, project_type)
                
                if session_key in self.session_cache:
                    print(f"Using cached data for {session_key}")
                    cached_data = self.session_cache[session_key]
                    
                    # Use cached data to maintain consistency
                    prompt = f"""You are a helpful construction cost advisor. 
                    
Previous conversation context:
{json.dumps(chat_history[-3:], indent=2)}

Current question: {query}

You previously provided this information for {project_type} remodel in {location}:
- Cost range: ${cached_data['cost_low']:,.0f} to ${cached_data['cost_high']:,.0f}
- Average cost: ${cached_data['cost_average']:,.0f}
- Timeline: {cached_data['timeline']} weeks

Use this EXACT same data to answer the current question. Do not change the numbers.
If asked about quality levels, explain what these numbers represent (e.g., if they're mid-range, high-end, etc.).
Maintain consistency with your previous answers."""
                    
                    response = await self.llm.ainvoke(prompt)
                    return {
                        "message": response.content,
                        "source_documents": []
                    }
            
            # If no cached data, search for new data
            search_query = query
            if location:
                search_query += f" {location}"
            if project_type:
                search_query += f" {project_type}"
            
            # Create embedding
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
            
            # Filter results
            filtered_matches = []
            for match in search_results.matches:
                if match.metadata:
                    if location and match.metadata.get('location') == location:
                        if project_type and project_type in match.metadata.get('remodel_type', '').lower():
                            filtered_matches.append(match)
            
            # If not enough matches, broaden search
            if len(filtered_matches) < 3:
                for match in search_results.matches:
                    if match.metadata:
                        if location and match.metadata.get('location') == location:
                            filtered_matches.append(match)
            
            if not filtered_matches:
                filtered_matches = search_results.matches[:5]
            
            # Get the best match and cache it
            best_match = filtered_matches[0]
            if best_match.metadata and session_key:
                # Cache this data for consistency
                self.session_cache[session_key] = {
                    'cost_low': best_match.metadata.get('cost_low', 0),
                    'cost_high': best_match.metadata.get('cost_high', 0),
                    'cost_average': best_match.metadata.get('cost_average', 0),
                    'timeline': best_match.metadata.get('timeline', 'Unknown'),
                    'project_type': best_match.metadata.get('remodel_type', ''),
                    'location': best_match.metadata.get('location', '')
                }
            
            # Format data for prompt
            data_summary = []
            for match in filtered_matches[:3]:
                if match.metadata:
                    meta = match.metadata
                    data_summary.append(
                        f"- {meta.get('remodel_type', '').replace('_', ' ').title()} in {meta.get('location', '')}: "
                        f"${meta.get('cost_low', 0):,.0f}-${meta.get('cost_high', 0):,.0f} "
                        f"(avg ${meta.get('cost_average', 0):,.0f}), {meta.get('timeline', 'Unknown')} weeks"
                    )
            
            data_text = "\n".join(data_summary)
            
            prompt = f"""You are a helpful construction cost advisor for California.

Current question: {query}

Available data:
{data_text}

Instructions:
1. Focus on the specific location and project type mentioned
2. Do not mention other cities unless specifically asked
3. Be consistent with any numbers you provide
4. If asked about quality levels, explain what the data represents

Provide a clear, helpful response."""
            
            response = await self.llm.ainvoke(prompt)
            
            return {
                "message": response.content,
                "source_documents": [match.metadata for match in filtered_matches[:3]]
            }
            
        except Exception as e:
            print(f"Error in get_chat_response: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "source_documents": []
            }