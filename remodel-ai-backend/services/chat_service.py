from typing import List, Dict, Any, Optional
from services.rag_service import RAGService
from services.session_service import SessionService
import logging
import uuid

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.rag_service = RAGService()
        self.session_service = SessionService()
    
    async def process_message(self, content: str, role: str = "user", session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a chat message and return response"""
        try:
            # Create or retrieve session
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Get session history
            session = self.session_service.get_session(session_id)
            chat_history = session.get("messages", [])
            
            # Convert chat history to the format expected by RAGService
            formatted_history = []
            for i in range(0, len(chat_history), 2):
                if i + 1 < len(chat_history):
                    human_msg = chat_history[i].get("content", "")
                    ai_msg = chat_history[i + 1].get("content", "")
                    formatted_history.append((human_msg, ai_msg))
            
            # Get response from RAG service - now with session_id
            response = await self.rag_service.get_chat_response(
                query=content,
                chat_history=formatted_history,
                session_id=session_id  # Pass session ID for caching
            )
            
            # Update session with new messages
            chat_history.append({"role": role, "content": content})
            chat_history.append({"role": "assistant", "content": response["message"]})
            
            self.session_service.update_session(
                session_id=session_id,
                messages=chat_history
            )
            
            return {
                "message": response["message"],
                "session_id": session_id,
                "source_documents": response.get("source_documents", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "message": "I encountered an error while processing your request. Please try again.",
                "session_id": session_id,
                "error": str(e)
            }