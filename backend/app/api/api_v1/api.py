"""
API v1 router aggregation.
"""
from fastapi import APIRouter
from backend.app.api.api_v1.endpoints import auth, chat

api_router = APIRouter()

# Include auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include chat endpoints
api_router.include_router(chat.router, tags=["chat"])
