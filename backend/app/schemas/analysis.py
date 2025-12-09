"""
Analysis schemas for word cloud, sentiment analysis, and intimacy scoring.
"""
from pydantic import BaseModel, Field
from typing import List


class WordCloudItem(BaseModel):
    """Schema for a word cloud item with word and frequency."""
    word: str = Field(..., description="The word or phrase")
    frequency: int = Field(..., ge=1, description="Frequency count of the word")


class SentimentResult(BaseModel):
    """Schema for sentiment analysis result."""
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Overall sentiment score from -1 (negative) to 1 (positive)")
    positive_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Positive sentiment probability")
    negative_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Negative sentiment probability")
    neutral_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Neutral sentiment probability")


class IntimacyResult(BaseModel):
    """Schema for intimacy scoring result."""
    intimacy_score: float = Field(..., ge=0.0, le=100.0, description="Intimacy score from 0 to 100")
    sentiment_factor: float = Field(..., description="Contribution from sentiment analysis")
    frequency_factor: float = Field(..., description="Contribution from interaction frequency")
    flow_factor: float = Field(..., description="Contribution from conversation flow")
    consecutive_factor: float = Field(..., description="Contribution from consecutive messages")


class AnalysisResponse(BaseModel):
    """Schema for comprehensive analysis response."""
    word_cloud: List[WordCloudItem] = Field(default_factory=list, description="Word cloud data")
    sentiment: SentimentResult = Field(..., description="Sentiment analysis result")
    intimacy: IntimacyResult = Field(..., description="Intimacy scoring result")
