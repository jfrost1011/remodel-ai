from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import chat, estimate, export
from config import settings
import logging
# Add test endpoint
from services.rag_service import RAGService
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== RemodelAI Starting ===")
    import os
    print("Available environment variables:")
    for key, value in os.environ.items():
        if any(x in key.lower() for x in ['key', 'password', 'secret']):
            print(f"{key}={'*' * 8}")
        else:
            print(f"{key}={value}")
    print("=== Starting application ===")
    yield
    print("=== Shutting down application ===")
app = FastAPI(
    title="RemodelAI API",
    description="AI-powered remodeling cost estimation API",
    version="1.0.0",
    lifespan=lifespan
)
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include routers
app.include_router(chat.router)
app.include_router(estimate.router)
app.include_router(export.router)
@app.get("/")
async def root():
    return {"message": "RemodelAI API is running"}
@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.environment}
# Debug endpoint
@app.get("/debug/pinecone")
async def debug_pinecone():
    try:
        rag = RAGService()
        test_query = "What are ADUs?"
        response = await rag.get_chat_response(test_query, [])
        return {
            "status": "success",
            "vectorstore_initialized": rag.vectorstore is not None,
            "qa_chain_initialized": rag.qa_chain is not None,
            "test_response": response
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(settings.port))
