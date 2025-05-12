from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from schemas import ExportRequest, ExportResponse
from services.pdf_service import PDFService
import logging
from datetime import datetime, timedelta
router = APIRouter()
logger = logging.getLogger(__name__)
pdf_service = PDFService()
@router.post("/", response_model=ExportResponse)
async def export_estimate(request: ExportRequest):
    """Export an estimate in the requested format"""
    try:
        if request.format == "pdf":
            file_path = await pdf_service.generate_estimate_pdf(
                estimate_id=request.estimate_id,
                include_breakdown=request.include_breakdown,
                include_similar_projects=request.include_similar_projects
            )
            return ExportResponse(
                file_url=f"/api/v1/export/download/{request.estimate_id}",
                download_name=f"estimate_{request.estimate_id}.pdf",
                expires_at=datetime.now() + timedelta(hours=1)
            )
        else:
            raise HTTPException(status_code=400, detail=f"Format {request.format} not yet implemented")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error exporting estimate")
@router.get("/download/{estimate_id}")
async def download_export(estimate_id: str):
    """Download an exported file"""
    try:
        file_path = pdf_service.get_export_path(estimate_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Export not found")
        return FileResponse(
            path=file_path,
            filename=f"estimate_{estimate_id}.pdf",
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error downloading file")