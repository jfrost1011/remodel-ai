import os
from typing import Optional, List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from pinecone import Pinecone as PineconeClient
from config import settings
class RAGService:
    def __init__(self):
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            temperature=0.7
        )
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model
        )
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
                self.vectorstore = None
            else:
                # Initialize vector store
                self.vectorstore = Pinecone.from_existing_index(
                    index_name=settings.pinecone_index,
                    embedding=self.embeddings
                )
                print("Pinecone vector store initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {str(e)}")
            import traceback
            traceback.print_exc()
            self.vectorstore = None
    async def get_chat_response(self, query: str, chat_history: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Get response from the RAG system"""
        if not self.vectorstore:
            return {
                "message": "I don't know.",
                "source_documents": []
            }
        try:
            # Search for relevant documents
            docs = self.vectorstore.similarity_search(query, k=5)
            if not docs:
                return {
                    "message": "I don't know.",
                    "source_documents": []
                }
            # Extract context from documents
            context = "\n\n".join([doc.page_content for doc in docs])
            # Create prompt
            prompt = f"""You are a construction cost estimation assistant specializing in California remodeling projects, specifically serving San Diego and Los Angeles.
Based on the construction data below, provide accurate cost estimates, timelines, and material recommendations.
Construction data:
{context}
Question: {query}
Answer:"""
            # Get completion from LLM
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
                "message": "I don't know.",
                "source_documents": []
            }
