from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api import chat, estimate, export
from config import settings
import os
app = FastAPI(
    title="RemodelAI API",
    description="API for construction cost estimation in California",
    version="1.0.0"
)
# Configure CORS - be very permissive for now
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://remodel-ai-gi1l.vercel.app",
    "https://remodel-ai.vercel.app",
    "https://*.vercel.app",
    settings.frontend_url,
]
# Add wildcard for all vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(estimate.router, prefix="/api/v1/estimate", tags=["estimate"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])
@app.get("/")
async def root():
    return {"message": "RemodelAI API", "status": "healthy", "version": "1.0.0"}
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
@app.get("/debug/env")
async def debug_environment():
    """Debug endpoint to check environment variables"""
    return {
        "railway_environment": os.environ.get("RAILWAY_ENVIRONMENT", "not set"),
        "port": os.environ.get("PORT", "not set"),
        "openai_api_key": "set" if os.environ.get("OPENAI_API_KEY") else "not set",
        "pinecone_api_key": "set" if os.environ.get("PINECONE_API_KEY") else "not set",
        "pinecone_index": os.environ.get("PINECONE_INDEX", "not set"),
        "frontend_url": settings.frontend_url,
        "cors_origins": ["*"],
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
