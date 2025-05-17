from dotenv import load_dotenv
import os

# Try to load dotenv, but don't fail if it doesn't work
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Continuing with default settings...")

from typing import Dict, Any, Optional
from dataclasses import dataclass
import redis


@dataclass
class Settings:
    # API Keys - get from environment
    openai_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index: str = "remodel-ai-mvp"
    serp_api_key: str = ""
    
    # URLs
    frontend_url: str = "http://localhost:3000"
    
    # OpenAI Settings
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-ada-002"
    
    # App Settings
    environment: str = "development"
    port: int = 8000
    
    # Redis settings
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    session_ttl: int = 3600  # 1-hour TTL for sessions
    
    # ────────────────────────────────────────────────────────────
    #  Updated Redis connector
    # ────────────────────────────────────────────────────────────
    def get_redis_connection(self):
        """Return a Redis client or None if Redis is disabled/unavailable."""
        # If the user explicitly disabled Redis, skip connection attempt
        if os.environ.get("USE_REDIS", "").lower() == "false":
            print("DEBUG: Redis is disabled via USE_REDIS environment variable")
            return None
        
        # Attempt to establish a Redis connection
        try:
            if self.redis_url:
                return redis.from_url(self.redis_url, decode_responses=True)
            else:
                return redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                    decode_responses=True,
                )
        except Exception as e:
            print(f"DEBUG: Could not connect to Redis: {e}")
            return None


# Create settings instance with environment variables
settings = Settings(
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    pinecone_api_key=os.getenv("PINECONE_API_KEY", ""),
    pinecone_index=os.getenv("PINECONE_INDEX", "remodel-ai-mvp"),
    serp_api_key=os.getenv("SERP_API_KEY", ""),
    frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
    openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
    environment=os.getenv("ENVIRONMENT", "development"),
    port=int(os.getenv("PORT", "8000")),
    redis_url=os.getenv("REDIS_URL"),
    redis_host=os.getenv("REDIS_HOST", "localhost"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db=int(os.getenv("REDIS_DB", "0")),
    session_ttl=int(os.getenv("SESSION_TTL", "3600")),
)

# Cache for estimates
estimates_cache: Dict[str, Any] = {}

# Debug: show Redis configuration details
if settings.redis_url:
    print(f"DEBUG: Redis URL loaded: {settings.redis_url[:20]}...")
else:
    print("DEBUG: No Redis URL found, using host/port configuration")
    print(f"DEBUG: Redis host: {settings.redis_host}, port: {settings.redis_port}")


# Test Redis connection (only if Redis is not disabled)
def test_redis_connection():
    redis_client = settings.get_redis_connection()
    if redis_client is None:
        print("DEBUG: Redis disabled or unavailable; skipping connection test")
        return False

    try:
        redis_client.ping()
        print("DEBUG: Redis connection successful!")
        return True
    except Exception as e:
        print(f"DEBUG: Redis connection failed: {e}")
        return False


# Run the Redis connectivity test when the module loads
print("DEBUG: Testing Redis connection...")
test_redis_connection()
