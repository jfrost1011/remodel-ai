from typing import Dict, Any, List, Optional
from config import settings, chat_sessions
from services.rag_service import RAGService
import logging
import re
logger = logging.getLogger(__name__)
class ChatService:
    def __init__(self):
        self.rag_service = RAGService()
    async def process_message(self, content: str, role: str, session_id: str) -> Dict[str, Any]:
        """Process a chat message and return response"""
        try:
            # Validate query scope
            if not self._is_construction_related(content):
                return {
                    "message": "I'm specifically trained in California residential construction. I can help with remodeling, additions, ADUs, permits, costs, and financing. What construction questions can I answer for you?",
                    "type": "text",
                    "metadata": {"filtered": True}
                }
            # Check geographic constraints if location is mentioned
            location = self._extract_location(content)
            if location and not self._is_california_location(location):
                return {
                    "message": f"We're not available in {location} yet, but we're expanding soon! I can help with construction projects in California, particularly San Diego and Los Angeles.",
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
            'square', 'footage', 'sq ft', 'budget', 'timeline'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in construction_keywords)
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query"""
        # Common location patterns
        patterns = [
            r'in (\w+)',
            r'at (\w+)',
            r'near (\w+)',
            r'around (\w+)',
            r'(\w+) area',
            r'(\w+) region'
        ]
        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return match.group(1).title()
        return None
    def _is_california_location(self, location: str) -> bool:
        """Check if location is in California"""
        ca_locations = [
            'california', 'ca', 'san diego', 'los angeles', 'la', 'sd',
            'orange county', 'san francisco', 'sf', 'sacramento',
            'san jose', 'oakland', 'fresno', 'long beach'
        ]
        location_lower = location.lower()
        return any(ca_loc in location_lower for ca_loc in ca_locations)