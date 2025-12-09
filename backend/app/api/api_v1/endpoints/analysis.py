"""
Analysis endpoints for sentiment analysis, word cloud generation, and intimacy scoring.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from backend.app.schemas.analysis import (
    SentimentAnalysisRequest,
    SentimentResult,
    WordCloudRequest,
    WordCloudItem,
    IntimacyAnalysisRequest,
    IntimacyResult
)
from backend.app.services.analysis_service import (
    analyze_sentiment_llm,
    generate_word_cloud,
    calculate_intimacy
)

router = APIRouter()


@router.post("/sentiment", response_model=SentimentResult)
def analyze_sentiment(request: SentimentAnalysisRequest):
    """
    Analyze text sentiment using LLM (Qwen/DashScope).
    
    Args:
        request: SentimentAnalysisRequest containing text to analyze
        
    Returns:
        SentimentResult with sentiment scores
        
    Raises:
        HTTPException: If sentiment analysis fails or API key is not configured
    """
    try:
        result = analyze_sentiment_llm(request.text)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}"
        )


@router.post("/wordcloud", response_model=List[WordCloudItem])
def generate_wordcloud(request: WordCloudRequest):
    """
    Generate word cloud data from a list of messages.
    
    Args:
        request: WordCloudRequest containing messages and optional top_n parameter
        
    Returns:
        List of WordCloudItem with word and frequency data
        
    Raises:
        HTTPException: If word cloud generation fails
    """
    try:
        result = generate_word_cloud(request.messages, request.top_n)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Word cloud generation failed: {str(e)}"
        )


@router.post("/intimacy", response_model=IntimacyResult)
def calculate_intimacy_score(request: IntimacyAnalysisRequest):
    """
    Calculate intimacy score based on message history and interaction patterns.
    
    Args:
        request: IntimacyAnalysisRequest containing sentiment scores, message count, 
                 sender info, and consecutive message counts
        
    Returns:
        IntimacyResult with intimacy score and contributing factors
        
    Raises:
        HTTPException: If intimacy calculation fails
    """
    try:
        result = calculate_intimacy(
            sentiment_scores=request.sentiment_scores,
            message_count=request.message_count,
            last_sender_id=request.last_sender_id,
            current_user_id=request.current_user_id,
            consecutive_messages=request.consecutive_messages
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intimacy calculation failed: {str(e)}"
        )
