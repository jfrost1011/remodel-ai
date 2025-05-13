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
            'project', 'construction', 'contractor', 'materials', 'labor', 'permit'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in construction_keywords)
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
            # Create embedding using OpenAI directly
            print(f"Creating embedding for query: {query}")
            embedding_response = self.openai_client.embeddings.create(
                input=query,
                model=settings.embedding_model
            )
            query_embedding = embedding_response.data[0].embedding
            # Search for relevant documents in Pinecone
            print(f"Searching Pinecone for relevant documents...")
            search_results = self.index.query(
                vector=query_embedding,
                top_k=5,
                include_metadata=True,
                namespace=""
            )
            print(f"Found {len(search_results.matches)} matches")
            if not search_results.matches:
                print("No documents found")
                return {
                    "message": "I'm sorry, I don't have specific cost data for that type of project. Could you provide more details about what kind of remodeling project you're interested in?",
                    "source_documents": []
                }
            # Extract and format context
            context_parts = []
            docs = []
            # Group similar projects
            project_groups = {}
            for match in search_results.matches:
                if match.metadata:
                    key = f"{match.metadata.get('remodel_type', '')}_{match.metadata.get('location', '')}"
                    if key not in project_groups:
                        project_groups[key] = []
                    project_groups[key].append(match.metadata)
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
            context = "\n".join(context_parts)
            # Create a focused prompt
            prompt = f"""You are a helpful construction cost advisor for California, specifically serving San Diego and Los Angeles. 
Based on the data below, provide a concise, conversational response about construction costs.
Data:
{context}
Question: {query}
Provide a brief, friendly response focusing on the most relevant information. Include cost ranges and timelines where appropriate."""
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
