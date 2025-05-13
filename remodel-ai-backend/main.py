from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import chat, estimate, export
from config import settings
import logging
from datetime import datetime
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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
    lifespan=lifespan,
    redirect_slashes=False  # Disable automatic slash redirects
)

# CORS middleware with specific origins
allowed_origins = [
    "https://remodel-ai.vercel.app",
    "https://remodel-ai-*.vercel.app",  # For preview deployments
    "http://localhost:3000",  # For local development
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"Request: {request.method} {request.url.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Origin: {request.headers.get('origin', 'No origin header')}")
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Response status: {response.status_code} - Time: {process_time}s")
    return response

# Include routers with proper prefixes
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(estimate.router, prefix="/api/v1/estimate", tags=["estimate"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "RemodelAI API is running"}

@app.get("/api/v1/health")
async def health_check():
    logger.info("Health check accessed")
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

# New debug endpoint to check data
@app.post("/api/v1/debug/search")
async def debug_search(location: str, project_type: str):
    """Debug endpoint to see what data we're finding in Pinecone"""
    try:
        rag_service = RAGService()
        
        # Create a search query
        search_query = f"{project_type} remodel {location} cost estimate"
        
        # Create embedding
        embedding_response = rag_service.openai_client.embeddings.create(
            input=search_query,
            model="text-embedding-ada-002"
        )
        query_embedding = embedding_response.data[0].embedding
        
        # Search Pinecone
        search_results = rag_service.index.query(
            vector=query_embedding,
            top_k=10,
            include_metadata=True,
            namespace=""
        )
        
        # Format results
        results = []
        for match in search_results.matches:
            if match.metadata:
                results.append({
                    "score": match.score,
                    "location": match.metadata.get('location'),
                    "project_type": match.metadata.get('remodel_type'),
                    "cost_low": match.metadata.get('cost_low'),
                    "cost_high": match.metadata.get('cost_high'),
                    "cost_average": match.metadata.get('cost_average'),
                    "timeline": match.metadata.get('timeline')
                })
        
        return {
            "search_query": search_query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(settings.port))