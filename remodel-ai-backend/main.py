# main.py
# ───────────────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import gc            # used for graceful shutdown
import os
import asyncio       # needed for final task-cancellation sweep

# Internal routers / services
from api import chat, estimate, export
from config import settings
from services.rag_service import RAGService

# ═════════════════════════════════════════════════════════════════════════
#  Redis override – force in-memory storage instead of Redis
# ═════════════════════════════════════════════════════════════════════════
os.environ["USE_REDIS"] = "False"   # ← NEW LINE

# ── logging setup ─────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── lifespan (startup / shutdown banner) ──────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== RemodelAI Starting ===")
    print("Available environment variables:")
    for key, value in os.environ.items():
        if any(x in key.lower() for x in ["key", "password", "secret"]):
            print(f"{key}={'*' * 8}")
        else:
            print(f"{key}={value}")
    print("=== Starting application ===")
    yield
    print("=== Shutting down application ===")

# ── FastAPI app ───────────────────────────────────────────────────────────
app = FastAPI(
    title="RemodelAI API",
    description="AI-powered remodeling cost estimation API",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# ═════════════════════════════════════════════════════════════════════════
#  CORS
# ═════════════════════════════════════════════════════════════════════════
allowed_origins = [
    "https://remodel-ai.vercel.app",
    "https://remodel-ai-*.vercel.app",  # preview deployments
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # loosened for debugging – tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ═════════════════════════════════════════════════════════════════════════
#  Request-logging middleware
# ═════════════════════════════════════════════════════════════════════════
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.now()
    logger.info(f"Request: {request.method} {request.url.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Origin: {request.headers.get('origin', 'No origin header')}")
    response = await call_next(request)
    duration = (datetime.now() - start).total_seconds()
    logger.info(f"Response: {response.status_code} – {duration}s")
    return response

# ═════════════════════════════════════════════════════════════════════════
#  Graceful shutdown – close all RAGService aiohttp sessions
# ═════════════════════════════════════════════════════════════════════════
@app.on_event("shutdown")
async def shutdown_event():
    """Ensure any RAGService instances still in memory close their aiohttp sessions."""
    from services.rag_service import RAGService  # local import to avoid circular refs

    # Force garbage collection so we catch recently dereferenced objects
    gc.collect()

    closed = 0
    for obj in gc.get_objects():
        if isinstance(obj, RAGService):
            if (
                hasattr(obj, "aiohttp_session")
                and obj.aiohttp_session
                and not obj.aiohttp_session.closed
            ):
                try:
                    await obj.close()
                    closed += 1
                except Exception as e:
                    logger.error(f"Error closing aiohttp session: {e}")

    logger.info(f"Closed {closed} RAGService aiohttp sessions on shutdown")

    # Final sweep: cancel any lingering asyncio tasks to avoid warnings
    tasks = [
        t for t in asyncio.all_tasks()
        if t is not asyncio.current_task() and not t.done()
    ]
    for task in tasks:
        task.cancel()

    logger.info("Application shutdown complete")

# ═════════════════════════════════════════════════════════════════════════
#  Routers
# ═════════════════════════════════════════════════════════════════════════
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(estimate.router, prefix="/api/v1/estimate", tags=["estimate"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])

# ═════════════════════════════════════════════════════════════════════════
#  Basic endpoints
# ═════════════════════════════════════════════════════════════════════════
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "RemodelAI API is running"}

@app.get("/api/v1/health")
async def health_check():
    logger.info("Health check accessed")
    return {"status": "healthy", "environment": settings.environment}

# ═════════════════════════════════════════════════════════════════════════
#  Debug endpoints
# ═════════════════════════════════════════════════════════════════════════
@app.get("/debug/pinecone")
async def debug_pinecone():
    try:
        rag = RAGService()
        test_query = "What are ADUs?"
        response = await rag.get_chat_response(test_query, [])
        return {
            "status": "success",
            "vectorstore_initialized": rag.vector_store is not None,
            "test_response": response,
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }

@app.post("/api/v1/debug/search")
async def debug_search(location: str, project_type: str):
    """
    Debug endpoint to inspect raw Pinecone data (very limited use).
    """
    try:
        rag_service = RAGService()

        # Build synthetic query → embedding
        search_query = f"{project_type} remodel {location} cost estimate"
        embedding_resp = rag_service.llm.embeddings.create(
            input=search_query, model="text-embedding-ada-002"
        )
        query_emb = embedding_resp.data[0].embedding

        # Low-level Pinecone search
        res = rag_service.vector_store._index.query(
            vector=query_emb, top_k=10, include_metadata=True
        )

        results = [
            {
                "score": m.score,
                "location": m.metadata.get("location"),
                "project_type": m.metadata.get("remodel_type"),
                "cost_low": m.metadata.get("cost_low"),
                "cost_high": m.metadata.get("cost_high"),
                "cost_avg": m.metadata.get("cost_average"),
                "timeline": m.metadata.get("timeline"),
            }
            for m in res.matches
        ]

        return {"query": search_query, "results": results}
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

# ── entrypoint when run directly ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(settings.port))
