from typing import Dict, Any, List, Optional
from config import settings, chat_sessions
from services.rag_service import RAGService
import logging
logger = logging.getLogger(__name__)
class ChatService:
    def __init__(self):
        self.rag_service = RAGService()
    async def process_message(self, content: str, role: str, session_id: str) -> Dict[str, Any]:
        """Process a chat message and return response"""
        try:
            # First check if it's construction-related
            if not self._is_construction_related(content):
                return {
                    "message": "I'm specifically trained in California residential construction. I can help with remodeling, additions, ADUs, permits, costs, and financing. What construction questions can I answer for you?",
                    "type": "text",
                    "metadata": {"filtered": True}
                }
            # Get or create session
            if session_id not in chat_sessions:
                chat_sessions[session_id] = []
            # Add user message to history
            chat_sessions[session_id].append({
                "role": role,
                "content": content
            })
            # Get response from RAG system
            response = await self.rag_service.get_chat_response(
                query=content,
                chat_history=chat_sessions[session_id]
            )
            # Add assistant response to history
            chat_sessions[session_id].append({
                "role": "assistant",
                "content": response["message"]
            })
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        return chat_sessions.get(session_id, [])
    def _is_construction_related(self, query: str) -> bool:
        """Check if query is related to construction"""
        construction_keywords = [
            'remodel', 'renovation', 'addition', 'adu', 'permit', 'cost', 
            'build', 'construction', 'contractor', 'design', 'kitchen',
            'bathroom', 'zoning', 'finance', 'loan', 'estimate', 'project',
            'floor', 'roof', 'foundation', 'electrical', 'plumbing',
            'square', 'footage', 'sq ft', 'budget', 'timeline', 'price',
            'how much', 'quote', 'expense'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in construction_keywords)