"""
Message schemas for chat functionality.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    sender_id: int
    receiver_id: int
    content: str
    sentiment_score: Optional[float] = None
    positive_score: Optional[float] = None
    negative_score: Optional[float] = None
    neutral_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
