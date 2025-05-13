import os
from typing import Optional, List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from pinecone import Pinecone as PineconeClient
from config import settings
class RAGService:
    def __init__(self):
        print("Initializing RAG Service...")
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
        print(f"Getting chat response for query: {query}")
        if not self.vectorstore:
            print("No vectorstore available")
            return {
                "message": "I'm sorry, but I'm having trouble accessing the construction database. Please check back later.",
                "source_documents": []
            }
        try:
            # Search for relevant documents
            print(f"Searching for documents with query: {query}")
            docs = self.vectorstore.similarity_search(query, k=5)
            print(f"Found {len(docs)} documents")
            if not docs:
                print("No documents found")
                return {
                    "message": "I couldn't find specific information about that. Can you please rephrase your question?",
                    "source_documents": []
                }
            # Extract context from documents
            context = "\n\n".join([doc.page_content for doc in docs])
            print(f"Context length: {len(context)} characters")
            # Create prompt
            prompt = f"""You are a construction cost estimation assistant specializing in California remodeling projects, specifically serving San Diego and Los Angeles.
Based on the construction data below, provide accurate cost estimates, timelines, and material recommendations.
Construction data:
{context}
Question: {query}
Answer:"""
            print("Calling LLM...")
            # Get completion from LLM
            response = await self.llm.ainvoke(prompt)
            print(f"LLM response: {response.content[:100]}...")
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
