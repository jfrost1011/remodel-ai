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
            temperature=0.7
        )
        
        # Initialize OpenAI client directly
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Initialize Pinecone with better error handling
        try:
            # Initialize Pinecone client
            pc = PineconeClient(api_key=settings.pinecone_api_key)
            
            # Check if index exists
            indexes = pc.list_indexes()
            index_names = [idx.name for idx in indexes.indexes] if hasattr(indexes, 'indexes') else [idx.name for idx in indexes]
            
            print(f"Available Pinecone indexes: {index_names}")
            print(f"Looking for index: {settings.pinecone_index}")
            
            if settings.pinecone_index not in index_names:
                print(f"Warning: Pinecone index '{settings.pinecone_index}' not found.")
                self.index = None
            else:
                # Initialize Pinecone index
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
            'average', 'typical', 'usually', 'timeframe', 'long', 'weeks', 'months'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in construction_keywords)
    
    def extract_project_context(self, query: str, chat_history: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Extract comprehensive context from conversation"""
        context = {
            'location': None,
            'project_type': None,
            'asking_timeline': False,
            'asking_cost': False,
            'previous_project': None,
            'previous_location': None
        }
        
        query_lower = query.lower()
        
        # Check what the query is asking about
        if any(word in query_lower for word in ['timeline', 'long', 'duration', 'weeks', 'months', 'time', 'how long']):
            context['asking_timeline'] = True
        if any(word in query_lower for word in ['cost', 'price', 'much', 'estimate', 'budget', 'average']):
            context['asking_cost'] = True
        
        # Extract location from current query
        if 'san diego' in query_lower:
            context['location'] = 'San Diego'
        elif 'los angeles' in query_lower or ' la ' in query_lower or 'l.a.' in query_lower:
            context['location'] = 'Los Angeles'
        
        # Extract project type from current query
        project_types = {
            'kitchen': ['kitchen'],
            'bathroom': ['bathroom', 'bath'],
            'room_addition': ['room addition', 'addition'],
            'adu': ['adu', 'accessory dwelling'],
            'garage': ['garage'],
            'landscaping': ['landscaping', 'landscape'],
            'pool': ['pool'],
            'deck': ['deck'],
            'patio': ['patio']
        }
        
        for project_key, keywords in project_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    context['project_type'] = project_key
                    break
        
        # If we don't have full context, check recent conversation
        for i, (human, ai) in enumerate(reversed(chat_history[-5:])):  # Check last 5 exchanges
            human_lower = human.lower()
            ai_lower = ai.lower()
            
            # Extract location from history
            if not context['location']:
                if 'san diego' in human_lower or 'san diego' in ai_lower:
                    context['location'] = 'San Diego'
                    if i == 0:  # Most recent exchange
                        context['previous_location'] = 'San Diego'
                elif 'los angeles' in human_lower or ' la ' in human_lower or 'los angeles' in ai_lower:
                    context['location'] = 'Los Angeles'
                    if i == 0:
                        context['previous_location'] = 'Los Angeles'
            
            # Extract project type from history
            if not context['project_type']:
                for project_key, keywords in project_types.items():
                    for keyword in keywords:
                        if keyword in human_lower or keyword in ai_lower:
                            context['project_type'] = project_key
                            if i == 0:  # Most recent exchange
                                context['previous_project'] = project_key
                            break
        
        # If this is a follow-up question about timeline or cost, use previous context
        if (context['asking_timeline'] or context['asking_cost']) and not context['project_type']:
            context['project_type'] = context['previous_project']
            
        if (context['asking_timeline'] or context['asking_cost']) and not context['location']:
            context['location'] = context['previous_location']
        
        return context

    async def get_chat_response(self, query: str, chat_history: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Get response from the RAG system"""
        print(f"Getting chat response for query: {query}")
        
        # Check if this is a construction-related query
        if not self.is_construction_query(query):
            # Handle general conversation
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
            # Extract comprehensive context from conversation
            context = self.extract_project_context(query, chat_history)
            print(f"Extracted context: {context}")
            
            # If we're missing critical context for a follow-up question
            if (context['asking_timeline'] or context['asking_cost']) and not (context['location'] and context['project_type']):
                return {
                    "message": "I need more information to answer that. Could you tell me what type of project and which city (San Diego or Los Angeles) you're asking about?",
                    "source_documents": []
                }
            
            # Build search query with context
            search_query = query
            if context['project_type'] and context['project_type'] not in query.lower():
                search_query = f"{context['project_type']} {query}"
            if context['location'] and context['location'].lower() not in query.lower():
                search_query = f"{search_query} {context['location']}"
            
            # Create embedding using OpenAI directly
            print(f"Creating embedding for query: {search_query}")
            embedding_response = self.openai_client.embeddings.create(
                input=search_query,
                model=settings.embedding_model
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Search for relevant documents in Pinecone
            print(f"Searching Pinecone for relevant documents...")
            search_results = self.index.query(
                vector=query_embedding,
                top_k=10,
                include_metadata=True,
                namespace=""
            )
            
            print(f"Found {len(search_results.matches)} matches")
            
            # Filter results by context
            filtered_matches = []
            for match in search_results.matches:
                if match.metadata:
                    # Filter by location if specified
                    location_match = True
                    if context['location']:
                        location_match = match.metadata.get('location') == context['location']
                    
                    # Filter by project type if specified
                    project_match = True
                    if context['project_type']:
                        metadata_type = match.metadata.get('remodel_type', '').lower()
                        project_match = context['project_type'].replace('_', ' ') in metadata_type or context['project_type'] in metadata_type
                    
                    if location_match and project_match:
                        filtered_matches.append(match)
            
            # If we filtered too much, expand search
            if len(filtered_matches) < 3:
                filtered_matches = [m for m in search_results.matches if m.metadata.get('location') == context['location']][:5]
                print(f"Expanded search to location only, found {len(filtered_matches)} matches")
            
            if not filtered_matches:
                return {
                    "message": f"I don't have specific data for {context['project_type']} in {context['location']}. However, I can provide estimates for other project types in that area if you're interested.",
                    "source_documents": []
                }
            
            # Extract and format context
            context_parts = []
            docs = []
            
            # Group similar projects
            project_groups = {}
            for match in filtered_matches[:5]:
                if match.metadata:
                    key = f"{match.metadata.get('remodel_type', '')}_{match.metadata.get('location', '')}"
                    if key not in project_groups:
                        project_groups[key] = []
                    project_groups[key].append(match.metadata)
                    docs.append(match.metadata)
            
            # Format grouped data
            for key, group in project_groups.items():
                if group:
                    # Average the costs across similar projects
                    avg_low = sum(p.get('cost_low', 0) for p in group) / len(group)
                    avg_high = sum(p.get('cost_high', 0) for p in group) / len(group)
                    avg_cost = sum(p.get('cost_average', 0) for p in group) / len(group)
                    
                    project_type = group[0].get('remodel_type', '').replace('_', ' ').title()
                    location = group[0].get('location', 'Unknown')
                    timeline = group[0].get('timeline', 'Unknown')
                    
                    context_parts.append(f"{project_type} in {location}: ${avg_low:,.0f}-${avg_high:,.0f} (avg ${avg_cost:,.0f}), {timeline} weeks")
            
            context_text = "\n".join(context_parts)
            
            # Create a focused prompt based on what's being asked
            if context['asking_timeline'] and not context['asking_cost']:
                prompt = f"""You are a helpful construction timeline advisor. Based on the data below, provide a brief response about project timelines.

Data:
{context_text}

User's previous conversation mentioned: {context['project_type']} in {context['location']}
Current question: {query}

Provide a brief, direct answer about the timeline for the specific project they're asking about."""
            
            elif context['asking_cost'] and not context['asking_timeline']:
                prompt = f"""You are a helpful construction cost advisor. Based on the data below, provide a brief response about project costs.

Data:
{context_text}

Context: The conversation is about {context['project_type']} in {context['location']}
Current question: {query}

Provide a brief, direct answer about the cost for the specific project they're asking about."""
            
            else:
                prompt = f"""You are a helpful construction cost advisor for California, specifically serving San Diego and Los Angeles.

Based on the data below, provide a concise response about construction costs and timelines.

Data:
{context_text}

Question: {query}

Provide a brief, friendly response with the most relevant information. Include both cost ranges and timelines if available."""
            
            print("Calling LLM...")
            response = await self.llm.ainvoke(prompt)
            
            return {
                "message": response.content,
                "source_documents": docs
            }
            
        except Exception as e:
            print(f"Error in get_chat_response: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "source_documents": []
            }