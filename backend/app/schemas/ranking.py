"""
Ranking schemas for friend ranking and relationship insights.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ActivityPoint(BaseModel):
    """Single day activity data point."""
    date: str = Field(..., description="Date in ISO format")
    count: int = Field(..., ge=0, description="Message count for the day")


class ScorePoint(BaseModel):
    """Single day score data point."""
    date: str = Field(..., description="Date in ISO format")
    score: float = Field(..., ge=0.0, le=100.0, description="Daily intimacy score")


class FriendRanking(BaseModel):
    """Schema for a friend ranking entry."""
    friend_id: int = Field(..., description="Friend user ID")
    username: str = Field(..., description="Friend username")
    full_name: Optional[str] = Field(None, description="Friend full name")
    intimacy_score: float = Field(..., ge=0.0, le=100.0, description="Calculated intimacy score")
    interaction_count: int = Field(..., ge=0, description="Number of interactions")
    positive_interactions: int = Field(..., ge=0, description="Count of positive interactions")
    negative_interactions: int = Field(..., ge=0, description="Count of negative interactions")
    last_interaction: Optional[datetime] = Field(None, description="Timestamp of last interaction")
    activity_trend: List[ActivityPoint] = Field(default_factory=list, description="Recent chat frequency trend")
    score_trend: List[ScorePoint] = Field(default_factory=list, description="Recent intimacy score trend")
    
    class Config:
        from_attributes = True
