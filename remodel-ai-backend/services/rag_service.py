import os
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
import pinecone
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
            pc = Pinecone(api_key=settings.pinecone_api_key)
            # Check if index exists
            indexes = pc.list_indexes()
            index_names = [idx.name for idx in indexes]
            if settings.pinecone_index not in index_names:
                print(f"Warning: Pinecone index '{settings.pinecone_index}' not found.")
                print(f"Available indexes: {index_names}")
                # Don't fail immediately - allow app to start
                self.vectorstore = None
                self.qa_chain = None
            else:
                # Initialize vector store
                self.vectorstore = Pinecone.from_existing_index(
                    index_name=settings.pinecone_index,
                    embedding=self.embeddings
                )
                self._setup_qa_chain()
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {str(e)}")
            self.vectorstore = None
            self.qa_chain = None
    def _setup_qa_chain(self):
        """Setup the QA chain if vectorstore is available"""
        if not self.vectorstore:
            return
        prompt_template = """You are a construction cost estimation assistant specializing in California remodeling projects, specifically serving San Diego and Los Angeles (not LA County). You ONLY provide estimates for these two cities.
When users mention:
- "LA" -> interpret as Los Angeles city
- "Los Angeles County" or "LA County" -> politely clarify you only serve Los Angeles city
- Any other California city -> politely inform them you only serve San Diego and Los Angeles
Based on the retrieved construction data, provide accurate cost estimates, timelines, and material recommendations. Format your responses clearly with cost breakdowns when applicable.
Context: {context}
Chat History: {chat_history}
Question: {question}
Answer:"""
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
            combine_docs_chain_type="stuff",
            verbose=False,
            return_source_documents=True
        )
    async def get_chat_response(self, query: str, chat_history: list) -> Dict[str, Any]:
        """Get response from the RAG system"""
        if not self.qa_chain:
            # Fallback response if Pinecone isn't initialized
            return {
                "message": "I'm currently having trouble accessing the construction database. However, I can still help with general questions about remodeling in San Diego and Los Angeles. What would you like to know?",
                "source_documents": []
            }
        try:
            response = await self.qa_chain.ainvoke({
                "question": query,
                "chat_history": chat_history
            })
            return {
                "message": response["answer"],
                "source_documents": response.get("source_documents", [])
            }
        except Exception as e:
            print(f"Error in get_chat_response: {str(e)}")
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "source_documents": []
            }

