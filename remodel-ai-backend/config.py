import os
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
# Create settings instance with environment variables
settings = Settings(
    openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
    pinecone_api_key=os.environ.get("PINECONE_API_KEY", ""),
    pinecone_index=os.environ.get("PINECONE_INDEX", "remodel-ai-mvp"),
    serp_api_key=os.environ.get("SERP_API_KEY", ""),
    frontend_url=os.environ.get("FRONTEND_URL", "http://localhost:3000"),
    openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    embedding_model=os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002"),
    environment=os.environ.get("ENVIRONMENT", "production" if os.environ.get("RAILWAY_ENVIRONMENT") else "development"),
    port=int(os.environ.get("PORT", "8000"))
)
# Validate required fields
if not settings.openai_api_key:
    print("ERROR: OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY is required")
if not settings.pinecone_api_key:
    print("ERROR: PINECONE_API_KEY not found in environment variables")
    raise ValueError("PINECONE_API_KEY is required")
# In-memory storage for MVP
estimates_cache: Dict[str, Any] = {}
chat_sessions: Dict[str, list] = {}
print(f"Config loaded successfully - Environment: {settings.environment}, Port: {settings.port}")
