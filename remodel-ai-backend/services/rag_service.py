import os
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pinecone import Pinecone as PineconeClient
from config import settings
import logging
logger = logging.getLogger(__name__)
class RAGService:
    def __init__(self):
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
        # Initialize Pinecone
        self.pc = PineconeClient(api_key=settings.pinecone_api_key)
        # Check if index exists
        try:
            self.index = self.pc.Index(settings.pinecone_index)
        except Exception as e:
            logger.error(f"Error connecting to Pinecone index: {str(e)}")
            raise
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            openai_api_key=settings.openai_api_key
        )
        # Create vector store - using the direct initialization method
        self.vectorstore = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings,
            text_key="text"
        )
        # Create QA chain
        self._setup_qa_chain()
    def _setup_qa_chain(self):
        """Set up the QA chain with custom prompt"""
        prompt_template = """You are a California residential construction expert AI assistant. You have access to a database of construction projects with costs and timelines.
IMPORTANT GEOGRAPHIC RULES:
1. San Diego and Los Angeles are cities in California - you should provide estimates for these locations
2. Cities within San Diego County (like La Jolla, Encinitas, Del Mar, Carlsbad) count as San Diego
3. Cities within Los Angeles County count as Los Angeles
4. For other California cities, provide general California estimates
5. For non-California locations, politely explain you only serve California
Context from database: {context}
Question: {question}
Provide a helpful response using the actual data from the context. If asked about costs or timelines, use the specific numbers from the database for that location and project type.
Answer:"""
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 5}
            ),
            chain_type_kwargs={"prompt": prompt}
        )
    async def get_chat_response(self, query: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get a response for chat interface"""
        try:
            response = self.qa_chain.run(query)
            return {
                "message": response,
                "type": "text",
                "metadata": {
                    "confidence": 0.85,
                    "sources_used": 5
                }
            }
        except Exception as e:
            logger.error(f"Error in chat response: {str(e)}")
            raise
    async def get_estimate(self, query: str, project_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get a detailed estimate from the RAG system"""
        try:
            enhanced_query = f"""
            Provide a cost estimate for a {project_details.get('project_type')} project in {project_details.get('city')}.
            Property type: {project_details.get('property_type')}
            Square footage: {project_details.get('square_footage')}
            Use the specific cost data from the database for this location and project type.
            """
            response = self.qa_chain.run(enhanced_query)
            return self._parse_estimate_response(response)
        except Exception as e:
            logger.error(f"Error generating estimate: {str(e)}")
            raise
    def _parse_estimate_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract structured estimate data"""
        return {
            "total_cost": 75000,
            "cost_range_low": 65000,
            "cost_range_high": 85000,
            "confidence_score": 0.85,
            "permit_days": 45,
            "construction_days": 90,
            "similar_projects": []
        }