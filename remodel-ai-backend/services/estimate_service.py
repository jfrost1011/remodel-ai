from typing import Dict, Any, Optional
from schemas import ProjectDetails, EstimateResponse, CostBreakdown, TimelineBreakdown, SimilarProject
from services.rag_service import RAGService
from services.material_price_service import MaterialPriceService
from config import estimates_cache
import uuid
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
class EstimateService:
    def __init__(self):
        self.rag_service = RAGService()
        self.material_service = MaterialPriceService()
    async def generate_estimate(self, project_details: ProjectDetails, session_id: Optional[str] = None) -> EstimateResponse:
        """Generate a detailed cost estimate"""
        try:
            # Query RAG system for estimate
            query = self._build_estimate_query(project_details)
            rag_response = await self.rag_service.get_estimate(query, project_details.dict())
            # Get material prices
            common_materials = self.material_service.get_common_materials(project_details.project_type)
            material_prices = self.material_service.get_material_prices(common_materials, project_details.city)
            # Parse RAG response and create estimate
            estimate_data = self._parse_rag_response(rag_response)
            # Create estimate object
            estimate_id = f"est_{uuid.uuid4().hex[:8]}"
            # Calculate cost breakdown
            total_cost = estimate_data["total_cost"]
            # Adjust for LA pricing (+12%)
            if project_details.city == "Los Angeles":
                total_cost *= 1.12
            cost_breakdown = CostBreakdown(
                materials=total_cost * 0.40,
                labor=total_cost * 0.35,
                permits=total_cost * 0.05,
                other=total_cost * 0.20,
                total=total_cost
            )
            # Calculate timeline
            timeline = TimelineBreakdown(
                planning_days=14,
                permit_days=estimate_data.get("permit_days", 30),
                construction_days=estimate_data.get("construction_days", 60),
                total_days=14 + estimate_data.get("permit_days", 30) + estimate_data.get("construction_days", 60)
            )
            # Create similar projects
            similar_projects = []
            for sp in estimate_data.get("similar_projects", []):
                similar_projects.append(SimilarProject(**sp))
            # Create response
            estimate = EstimateResponse(
                estimate_id=estimate_id,
                total_cost=total_cost,
                cost_range_low=estimate_data.get("cost_range_low", total_cost * 0.9),
                cost_range_high=estimate_data.get("cost_range_high", total_cost * 1.1),
                cost_breakdown=cost_breakdown,
                confidence_score=estimate_data.get("confidence_score", 0.85),
                timeline=timeline,
                similar_projects=similar_projects,
                created_at=datetime.now(),
                metadata={
                    "session_id": session_id,
                    "material_prices": material_prices
                } if session_id else {"material_prices": material_prices}
            )
            # Cache estimate
            estimates_cache[estimate_id] = estimate.dict()
            return estimate
        except Exception as e:
            logger.error(f"Error generating estimate: {str(e)}")
            raise
    def get_estimate(self, estimate_id: str) -> Optional[EstimateResponse]:
        """Retrieve a cached estimate"""
        estimate_data = estimates_cache.get(estimate_id)
        if estimate_data:
            return EstimateResponse(**estimate_data)
        return None
    def _build_estimate_query(self, project_details: ProjectDetails) -> str:
        """Build a query string for the RAG system"""
        return f"""
        Project Type: {project_details.project_type.value}
        Property Type: {project_details.property_type}
        Location: {project_details.city}, {project_details.state}
        Square Footage: {project_details.square_footage}
        Additional Details: {project_details.additional_details or 'None'}
        Please provide a detailed cost estimate including:
        1. Total cost estimate
        2. Cost range (low to high)
        3. Timeline estimate
        4. Similar projects with costs
        """
    def _parse_rag_response(self, rag_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the RAG response to extract estimate data"""
        return {
            "total_cost": rag_response.get("total_cost", 50000),
            "cost_range_low": rag_response.get("cost_range_low", 45000),
            "cost_range_high": rag_response.get("cost_range_high", 55000),
            "confidence_score": rag_response.get("confidence_score", 0.85),
            "permit_days": rag_response.get("permit_days", 30),
            "construction_days": rag_response.get("construction_days", 60),
            "similar_projects": rag_response.get("similar_projects", [])
        }