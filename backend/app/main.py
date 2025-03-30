# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

from app.api.v1.api import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Chat API",
    description="API for real-time voice chat with LLM and TTS.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health Check"])
async def read_root():
    """Health check endpoint."""
    logger.info("Root endpoint '/' called.")
    return {"status": "ok", "message": "Welcome to Voice Chat API!"}

if __name__ == "__main__":
    logger.info("Starting Uvicorn server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=5000, reload=True)