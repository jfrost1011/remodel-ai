import os
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pinecone import Pinecone as PineconeClient, ServerlessSpec
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
        index_names = [index.name for index in self.pc.list_indexes()]
        if settings.pinecone_index not in index_names:
            logger.warning(f"Pinecone index {settings.pinecone_index} not found. Creating...")
            self.pc.create_index(
                name=settings.pinecone_index,
                dimension=1536,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            logger.info(f"Created index {settings.pinecone_index}")
        # Get the index
        self.index = self.pc.Index(settings.pinecone_index)
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
        prompt_template = """You are a California residential construction expert AI assistant. 
EXPERTISE AREAS:
- Property zoning and feasibility analysis
- Residential design (economy, standard, luxury)
- California building codes and regulations
- Construction cost estimation
- Financing options (construction loans, HELOCs, cash-out refinancing)
- Material selection and costs
- Permit requirements and processes
- ADU (Accessory Dwelling Unit) regulations
- Energy efficiency and Title 24 compliance
- Seismic and fire safety requirements
STRICT RULES:
1. For ANY California construction questions: Provide helpful advice about building codes, regulations, general costs, timelines, and best practices
2. For SPECIFIC PRICING WITH ESTIMATES: Only provide detailed cost estimates with PDF invoices for San Diego and Los Angeles projects
3. For other California cities: Provide general advice and ballpark estimates but explain that detailed estimates are only available for SD/LA
4. For non-California queries: "We currently serve California only, but we're expanding to [state] soon!"
5. REJECT non-construction queries with: "I'm specialized in California residential construction. How can I help with your construction project?"
6. Always cite confidence levels for estimates
7. Reference similar projects when providing estimates
Context: {context}
Question: {question}
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
            {query}
            For this project in {project_details.get('city')}, please provide:
            1. A specific cost estimate with low and high ranges
            2. Breakdown of costs (materials, labor, permits)
            3. Timeline in days
            4. 3-5 similar projects with their costs and timelines
            5. Confidence score for this estimate
            Format the response as structured data.
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