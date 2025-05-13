import os
from typing import Optional, List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from pinecone import Pinecone as PineconeClient
import openai
from config import settings
import re
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
        
        # Initialize Pinecone with better error handling
        try:
            pc = PineconeClient(api_key=settings.pinecone_api_key)
            indexes = pc.list_indexes()
            index_names = [idx.name for idx in indexes.indexes] if hasattr(indexes, 'indexes') else [idx.name for idx in indexes]
            
            print(f"Available Pinecone indexes: {index_names}")
            print(f"Looking for index: {settings.pinecone_index}")
            
            if settings.pinecone_index not in index_names:
                print(f"Warning: Pinecone index '{settings.pinecone_index}' not found.")
                self.index = None
            else:
                self.index = pc.Index(settings.pinecone_index)
                print("Pinecone index initialized successfully")
                
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {str(e)}")
            import traceback
            traceback.print_exc()
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
    
    def extract_conversation_context(self, query: str, chat_history: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Extract context from the entire conversation"""
        # Build full conversation text
        conversation = []
        for human, ai in chat_history:
            conversation.append(f"Human: {human}")
            conversation.append(f"AI: {ai}")
        conversation.append(f"Human: {query}")
        
        full_conversation = "\n".join(conversation)
        
        # Use GPT to understand the conversation context
        context_prompt = f"""Analyze this conversation and extract the following information:
1. What location is being discussed? (San Diego or Los Angeles)
2. What type of project? (kitchen, bathroom, room addition, etc.)
3. What specific aspect is being asked about in the current question? (cost, timeline, quality level)
4. Is this a follow-up question to a previous topic?

Conversation:
{full_conversation}

Respond with a JSON object containing:
- location: the city being discussed (or null if unclear)
- project_type: the type of remodel (or null if unclear)
- aspect: what the current question is asking about
- is_followup: true if this relates to a previous question
- previous_context: any important context from earlier in the conversation
"""
        
        try:
            response = self.llm.invoke(context_prompt)
            context = json.loads(response.content)
            return context
        except:
            # Fallback to basic extraction
            return {
                'location': self._extract_location(full_conversation),
                'project_type': self._extract_project_type(full_conversation),
                'aspect': 'general',
                'is_followup': len(chat_history) > 0,
                'previous_context': ''
            }
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text"""
        text_lower = text.lower()
        if 'san diego' in text_lower:
            return 'San Diego'
        elif 'los angeles' in text_lower or ' la ' in text_lower:
            return 'Los Angeles'
        return None
    
    def _extract_project_type(self, text: str) -> Optional[str]:
        """Extract project type from text"""
        text_lower = text.lower()
        project_types = {
            'kitchen': ['kitchen'],
            'bathroom': ['bathroom', 'bath'],
            'room addition': ['room addition', 'addition'],
            'adu': ['adu', 'accessory dwelling'],
            'garage': ['garage'],
            'landscaping': ['landscaping', 'landscape']
        }
        
        for project_type, keywords in project_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return project_type
        return None

    async def get_chat_response(self, query: str, chat_history: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Get response from the RAG system"""
        print(f"Getting chat response for query: {query}")
        
        # Check if this is a construction-related query
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
            print("No Pinecone index available")
            return {
                "message": "I'm sorry, but I'm having trouble accessing the construction database. Please check back later.",
                "source_documents": []
            }
        
        try:
            # Extract conversation context
            context = self.extract_conversation_context(query, chat_history)
            print(f"Extracted context: {context}")
            
            # Build search query based on context
            search_parts = []
            if context.get('location'):
                search_parts.append(context['location'])
            if context.get('project_type'):
                search_parts.append(context['project_type'])
            search_parts.append(query)
            
            search_query = " ".join(search_parts)
            
            # Create embedding
            print(f"Creating embedding for query: {search_query}")
            embedding_response = self.openai_client.embeddings.create(
                input=search_query,
                model=settings.embedding_model
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Search Pinecone
            print(f"Searching Pinecone for relevant documents...")
            search_results = self.index.query(
                vector=query_embedding,
                top_k=10,
                include_metadata=True,
                namespace=""
            )
            
            print(f"Found {len(search_results.matches)} matches")
            
            # Filter by location if specified in context
            filtered_matches = []
            for match in search_results.matches:
                if match.metadata:
                    if context.get('location'):
                        if match.metadata.get('location') == context['location']:
                            filtered_matches.append(match)
                    else:
                        filtered_matches.append(match)
            
            # If too few matches, use all results
            if len(filtered_matches) < 3:
                filtered_matches = search_results.matches[:5]
            
            # Format the data
            data_points = []
            for match in filtered_matches[:5]:
                if match.metadata:
                    meta = match.metadata
                    data_points.append({
                        'project_type': meta.get('remodel_type', '').replace('_', ' ').title(),
                        'location': meta.get('location', 'Unknown'),
                        'cost_low': meta.get('cost_low', 0),
                        'cost_high': meta.get('cost_high', 0),
                        'cost_average': meta.get('cost_average', 0),
                        'timeline': meta.get('timeline', 'Unknown'),
                        'score': match.score
                    })
            
            # Create a smart prompt that maintains context
            data_summary = "\n".join([
                f"- {d['project_type']} in {d['location']}: ${d['cost_low']:,.0f}-${d['cost_high']:,.0f} (avg ${d['cost_average']:,.0f}), {d['timeline']} weeks"
                for d in data_points
            ])
            
            # Build conversation context for the prompt
            conversation_context = ""
            if chat_history:
                recent_history = chat_history[-3:]  # Last 3 exchanges
                conversation_context = "\nRecent conversation:\n"
                for human, ai in recent_history:
                    conversation_context += f"Human: {human}\n"
                    conversation_context += f"AI: {ai}\n"
            
            prompt = f"""You are a helpful construction cost advisor for California, specifically serving San Diego and Los Angeles.

{conversation_context}
Current question: {query}

Available data:
{data_summary}

Instructions:
1. If this is a follow-up question, use the context from the previous conversation
2. Always maintain consistency with previous answers
3. For the same project type and location, always provide the same costs and timelines
4. Be specific about which city and project type you're discussing
5. If asked about quality levels (high-end, mid-range, etc.), provide context about what the data represents

Provide a helpful, accurate response that maintains context from the conversation."""
            
            print("Calling LLM...")
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