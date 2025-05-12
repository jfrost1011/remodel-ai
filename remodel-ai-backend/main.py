from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from api import chat, estimate, export
import uvicorn
app = FastAPI(
    title="RemodelAI Estimator API",
    description="AI-powered construction cost estimation for San Diego and Los Angeles",
    version="1.0.0"
)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)