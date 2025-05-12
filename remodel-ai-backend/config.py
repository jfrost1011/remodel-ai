from pydantic_settings import BaseSettings
from typing import Dict, Any
import os
class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index: str = "remodel-ai-mvp"
    serp_api_key: str = ""
    # URLs
    frontend_url: str = "http://localhost:3000"
    # OpenAI Settings
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-ada-002"
    # App Settings
    environment: str = "development"
    class Config:
        env_file = ".env"
        case_sensitive = False
settings = Settings()
# In-memory storage for MVP
estimates_cache: Dict[str, Any] = {}
chat_sessions: Dict[str, list] = {}