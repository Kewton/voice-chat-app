# app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import chat

api_router = APIRouter()

# Include endpoint routers here
api_router.include_router(chat.router, tags=["chat"])