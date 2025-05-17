from dotenv import load_dotenv
import os
load_dotenv()
from typing import Dict, Any, Optional
from dataclasses import dataclass
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
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    session_ttl: int = 3600  # 1 hour TTL for sessions
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
    redis_host=os.getenv("REDIS_HOST", "localhost"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db=int(os.getenv("REDIS_DB", "0")),
    session_ttl=int(os.getenv("SESSION_TTL", "3600"))
)

# Cache for estimates
estimates_cache: Dict[str, Any] = {}
