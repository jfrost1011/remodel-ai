import redis
import json
from typing import Dict, Any, Optional
from config import settings
import logging
logger = logging.getLogger(__name__)
class SessionService:
    def __init__(self):
        # For now, use in-memory storage if Redis is not available
        self.use_redis = False
        self.memory_sessions = {}
        try:
            # Try to connect to Redis if available
            if hasattr(settings, 'redis_url') and settings.redis_url:
                self.redis_client = redis.from_url(settings.redis_url)
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Connected to Redis for session storage")
        except Exception as e:
            logger.warning(f"Could not connect to Redis, using in-memory storage: {str(e)}")
            self.use_redis = False
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve a session by ID"""
        try:
            if self.use_redis:
                session_data = self.redis_client.get(f"session:{session_id}")
                if session_data:
                    return json.loads(session_data)
            else:
                if session_id in self.memory_sessions:
                    return self.memory_sessions[session_id]
            # Return empty session if not found
            return {"messages": []}
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return {"messages": []}
    def update_session(self, session_id: str, messages: list) -> None:
        """Update session with new messages"""
        try:
            session_data = {"messages": messages}
            if self.use_redis:
                self.redis_client.set(
                    f"session:{session_id}",
                    json.dumps(session_data),
                    ex=3600  # Expire after 1 hour
                )
            else:
                self.memory_sessions[session_id] = session_data
                # Limit in-memory sessions to prevent memory leak
                if len(self.memory_sessions) > 100:
                    # Remove oldest sessions
                    oldest_key = next(iter(self.memory_sessions))
                    del self.memory_sessions[oldest_key]
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
    def clear_session(self, session_id: str) -> None:
        """Clear a session"""
        try:
            if self.use_redis:
                self.redis_client.delete(f"session:{session_id}")
            else:
                if session_id in self.memory_sessions:
                    del self.memory_sessions[session_id]
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
