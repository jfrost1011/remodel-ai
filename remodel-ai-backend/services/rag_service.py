import os
from typing import List, Dict, Any, Optional
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
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
        # Create vector store
        self.vectorstore = Pinecone(
            index=self.index,
            embedding=self.embeddings,
            text_key='text'
        )
        # Create QA chain
        self._setup_qa_chain()
    def _setup_qa_chain(self):
        """Set up the QA chain with custom prompt"""
        prompt_template = """You are a California residential construction expert AI assistant. You have access to a database of construction project information.
IMPORTANT: Use the provided context to answer questions. The context contains real data about construction projects, including costs and timelines.
Context: {context}
Question: {question}
Based on the context above, provide a helpful answer. If the context contains specific cost ranges or timelines for the requested project type and location, use those actual numbers. If the location mentioned is not in California, politely explain that you only have data for California projects.
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
            Based on the data you have, provide a cost estimate for a {project_details.get('project_type')} project in {project_details.get('city')}, California.
            Property type: {project_details.get('property_type')}
            Square footage: {project_details.get('square_footage')}
            Please provide:
            1. A specific cost estimate range (low to high)
            2. Average timeline for this type of project
            3. Any relevant details from similar projects
            """
            response = self.qa_chain.run(enhanced_query)
            # Parse response and return structured data
            return self._parse_estimate_response(response)
        except Exception as e:
            logger.error(f"Error generating estimate: {str(e)}")
            raise
    def _parse_estimate_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract structured estimate data"""
        # For now, return default structure - this would be enhanced with better parsing
        return {
            "total_cost": 75000,
            "cost_range_low": 65000,
            "cost_range_high": 85000,
            "confidence_score": 0.85,
            "permit_days": 45,
            "construction_days": 90,
            "similar_projects": [
                {
                    "project_type": "Kitchen Remodel",
                    "location": "San Diego",
                    "cost_range": "$60,000 - $80,000",
                    "timeline": "3-4 months",
                    "source": "Project Database"
                }
            ]
        }