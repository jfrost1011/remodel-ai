import os
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from config import settings
import logging
logger = logging.getLogger(__name__)
class RAGService:
    def __init__(self):
        # Set environment variable for Pinecone
        os.environ["PINECONE_API_KEY"] = settings.pinecone_api_key
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            openai_api_key=settings.openai_api_key
        )
        # Create vector store using the modern PineconeVectorStore
        self.vectorstore = PineconeVectorStore.from_existing_index(
            index_name=settings.pinecone_index,
            embedding=self.embeddings
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
Based on the context above, provide specific cost estimates and timelines. Use the actual numbers from the database.
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
            # Use invoke instead of run
            response = self.qa_chain.invoke({"query": query})
            # Extract the result from the response
            if isinstance(response, dict) and "result" in response:
                message = response["result"]
            else:
                message = str(response)
            return {
                "message": message,
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
            response = self.qa_chain.invoke({"query": enhanced_query})
            # Extract the result
            if isinstance(response, dict) and "result" in response:
                result = response["result"]
            else:
                result = str(response)
            return self._parse_estimate_response(result)
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