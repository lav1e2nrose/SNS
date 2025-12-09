"""
Analysis service for word cloud generation, sentiment analysis, and intimacy scoring.
"""
import os
import jieba
import json
import math
import logging
from collections import Counter
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from backend.app.schemas.analysis import WordCloudItem, SentimentResult, IntimacyResult
from backend.app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Try to import dashscope, but make it optional
try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False


# Load stop words
STOP_WORDS_PATH = Path(__file__).parent.parent / "data" / "stopwords.txt"
STOP_WORDS = set()

if STOP_WORDS_PATH.exists():
    with open(STOP_WORDS_PATH, "r", encoding="utf-8") as f:
        STOP_WORDS = set(line.strip() for line in f if line.strip())


def generate_word_cloud(messages: List[str], top_n: int = 50) -> List[WordCloudItem]:
    """
    Generate word cloud data from a list of messages using jieba for Chinese segmentation.
    
    Args:
        messages: List of message content strings
        top_n: Number of top words to return (default: 50)
    
    Returns:
        List of WordCloudItem containing word and frequency
    """
    if not messages:
        return []
    
    # Combine all messages
    combined_text = " ".join(messages)
    
    # Segment text using jieba
    words = jieba.cut(combined_text)
    
    # Filter words: remove stop words, single characters, and non-meaningful tokens
    filtered_words = [
        word.strip() 
        for word in words 
        if len(word.strip()) > 1 and word.strip() not in STOP_WORDS
    ]
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Get top N words
    top_words = word_counts.most_common(top_n)
    
    # Convert to WordCloudItem schema
    return [
        WordCloudItem(word=word, frequency=freq)
        for word, freq in top_words
    ]


def analyze_sentiment_llm(text: str) -> SentimentResult:
    """
    Analyze sentiment of text using Qwen (DashScope) API.
    
    Args:
        text: Text content to analyze
    
    Returns:
        SentimentResult with sentiment scores
    
    Raises:
        ValueError: If DashScope API key is not configured or dashscope is not installed
    """
    if not DASHSCOPE_AVAILABLE:
        raise ValueError("dashscope library is not installed. Please install it with: pip install dashscope")
    
    if not settings.DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY is not configured in environment variables")
    
    # Set API key
    dashscope.api_key = settings.DASHSCOPE_API_KEY
    
    # Construct prompt for sentiment analysis
    prompt = f"""请分析以下文本的情感倾向，返回一个-1到1之间的情感分数，其中：
-1表示非常负面
0表示中性
1表示非常正面

同时给出正面、负面、中性的概率（三者之和为1）。

文本: {text}

请只返回JSON格式的结果，格式如下：
{{"sentiment_score": 0.5, "positive_score": 0.6, "negative_score": 0.1, "neutral_score": 0.3}}
"""
    
    try:
        # Call Qwen API
        response = Generation.call(
            model='qwen-turbo',
            prompt=prompt
        )
        
        if response.status_code == 200:
            # Parse response
            result_text = response.output.text.strip()
            
            # Extract JSON from response (handle potential markdown code blocks and various formats)
            # Try to find JSON content between various delimiters
            import re
            json_pattern = r'\{[^}]*"sentiment_score"[^}]*\}'
            json_match = re.search(json_pattern, result_text)
            
            if json_match:
                result_text = json_match.group()
            elif "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            result_data = json.loads(result_text)
            
            return SentimentResult(
                sentiment_score=result_data.get("sentiment_score", 0.0),
                positive_score=result_data.get("positive_score", 0.33),
                negative_score=result_data.get("negative_score", 0.33),
                neutral_score=result_data.get("neutral_score", 0.34)
            )
        else:
            # Fallback to neutral sentiment on API error
            return SentimentResult(
                sentiment_score=0.0,
                positive_score=0.33,
                negative_score=0.33,
                neutral_score=0.34
            )
    except Exception as e:
        # Log error and return neutral sentiment
        logger.error(f"Error in sentiment analysis: {e}", exc_info=True)
        return SentimentResult(
            sentiment_score=0.0,
            positive_score=0.33,
            negative_score=0.33,
            neutral_score=0.34
        )


def calculate_intimacy(
    sentiment_scores: List[float],
    message_count: int,
    last_sender_id: int,
    current_user_id: int,
    consecutive_messages: Dict[int, int]
) -> IntimacyResult:
    """
    Calculate intimacy score based on multiple factors.
    
    Args:
        sentiment_scores: List of sentiment scores from messages
        message_count: Total number of messages exchanged
        last_sender_id: ID of user who sent the last message
        current_user_id: ID of the current user
        consecutive_messages: Dictionary mapping user_id to count of consecutive messages
    
    Returns:
        IntimacyResult with intimacy score and contributing factors
    """
    # Factor 1: Sentiment Analysis (0-40 points)
    # Average sentiment score, normalized to 0-40 range
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
    sentiment_factor = ((avg_sentiment + 1) / 2) * 40  # Convert -1~1 to 0~40
    
    # Factor 2: Interaction Frequency (0-30 points)
    # More messages = higher frequency score
    # Use logarithmic scale to prevent over-weighting high message counts
    if message_count > 0:
        frequency_factor = min(30, math.log(message_count + 1) * 10)
    else:
        frequency_factor = 0.0
    
    # Factor 3: Conversation Flow (0-20 points)
    # Bonus if the other person sent the last message (shows they're initiating)
    flow_factor = 20.0 if last_sender_id != current_user_id else 10.0
    
    # Factor 4: Consecutive Messages (0-10 points)
    # Penalty for too many consecutive messages from one person
    max_consecutive = max(consecutive_messages.values()) if consecutive_messages else 0
    if max_consecutive <= 3:
        consecutive_factor = 10.0
    elif max_consecutive <= 5:
        consecutive_factor = 7.0
    elif max_consecutive <= 10:
        consecutive_factor = 4.0
    else:
        consecutive_factor = 0.0
    
    # Calculate total intimacy score (0-100)
    intimacy_score = sentiment_factor + frequency_factor + flow_factor + consecutive_factor
    intimacy_score = max(0.0, min(100.0, intimacy_score))  # Clamp to 0-100
    
    return IntimacyResult(
        intimacy_score=intimacy_score,
        sentiment_factor=sentiment_factor,
        frequency_factor=frequency_factor,
        flow_factor=flow_factor,
        consecutive_factor=consecutive_factor
    )
