from fastapi import APIRouter, HTTPException
from schemas import EstimateRequest, EstimateResponse
from services.estimate_service import EstimateService
import logging
router = APIRouter()
logger = logging.getLogger(__name__)
estimate_service = EstimateService()
@router.post("/", response_model=EstimateResponse)
async def create_estimate(request: EstimateRequest):
    """Create a new construction cost estimate"""
    try:
        estimate = await estimate_service.generate_estimate(
            project_details=request.project_details,
            session_id=request.session_id
        )
        return estimate
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Estimate error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating estimate")
@router.get("/{estimate_id}", response_model=EstimateResponse)
async def get_estimate(estimate_id: str):
    """Get an existing estimate by ID"""
    try:
        estimate = estimate_service.get_estimate(estimate_id)
        if not estimate:
            raise HTTPException(status_code=404, detail="Estimate not found")
        return estimate
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching estimate: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching estimate")