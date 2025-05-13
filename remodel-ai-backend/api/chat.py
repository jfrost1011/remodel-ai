from fastapi import APIRouter, HTTPException, Request
from schemas import ChatRequest, ChatResponse
from services.chat_service import ChatService
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
chat_service = ChatService()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for conversational AI interactions"""
    # Add debug logging
    logger.info(f"=== CHAT REQUEST RECEIVED ===")
    logger.info(f"Request content: {request.content}")
    logger.info(f"Request role: {request.role}")
    logger.info(f"Request session_id: {request.session_id}")
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Using session_id: {session_id}")
        
        response = await chat_service.process_message(
            content=request.content,
            role=request.role,
            session_id=session_id
        )
        
        logger.info(f"Chat service response received: {response}")
        
        chat_response = ChatResponse(
            message=response["message"],
            type=response.get("type", "text"),
            metadata=response.get("metadata"),
            session_id=session_id
        )
        
        logger.info(f"Returning response: {chat_response.dict()}")
        return chat_response
        
    except ValueError as e:
        logger.error(f"ValueError in chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your message")

@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        history = chat_service.get_session_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching chat history")