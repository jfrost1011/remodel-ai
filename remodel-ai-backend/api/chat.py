from fastapi import APIRouter, HTTPException, Response
from schemas import ChatRequest, ChatResponse
from services.chat_service import ChatService
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
chat_service = ChatService()


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, response: Response):
    """Chat endpoint for conversational AI interactions"""
    # ── debug logging ────────────────────────────────────────────────────
    logger.info("=== CHAT REQUEST RECEIVED ===")
    logger.info(f"Request content: {request.content}")
    logger.info(f"Request role: {request.role}")
    logger.info(f"Request session_id: {request.session_id}")

    try:
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Using session_id: {session_id}")

        service_response = await chat_service.process_message(
            content=request.content,
            role=request.role,
            session_id=session_id,
        )

        logger.info(f"Chat service response received: {service_response}")

        chat_response = ChatResponse(
            message=service_response["message"],
            type=service_response.get("type", "text"),
            metadata=service_response.get("metadata"),
            session_id=session_id,
        )

        # ── simple client-side caching rule ──────────────────────────────
        # Cache non-dynamic requests (no cost / price / timeline keywords)
        if not any(
            kw in request.content.lower()
            for kw in ["cost", "estimate", "price", "timeline", "time"]
        ):
            # Cache for 1 hour
            response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"

        logger.info(f"Returning response: {chat_response.dict()}")
        return chat_response

    except ValueError as e:
        logger.error(f"ValueError in chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred processing your message"
        )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        history = chat_service.get_session_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching chat history")
