"""
Friendship schemas for friend management.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FriendshipCreate(BaseModel):
    """Schema for creating a friendship request."""
    friend_id: int = Field(..., description="ID of the friend to add")


class FriendshipUpdate(BaseModel):
    """Schema for updating friendship status."""
    status: str = Field(..., description="Friendship status: pending, accepted, blocked")


class FriendshipResponse(BaseModel):
    """Schema for friendship response."""
    id: int
    user_id: int
    friend_id: int
    intimacy_score: float = 0.0
    interaction_count: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0
    status: str = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FriendResponse(BaseModel):
    """Schema for a friend user response."""
    id: int
    username: str
    full_name: Optional[str] = None
    intimacy_score: float = 0.0
    status: str = "pending"
    
    class Config:
        from_attributes = True
