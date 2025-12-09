"""
Tests for analysis endpoints and services.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.app.services.analysis_service import generate_word_cloud, calculate_intimacy


def test_word_cloud_generation_service():
    """Test word cloud generation with Chinese text."""
    messages = [
        "今天天气真好",
        "我很开心",
        "今天学习了很多新知识"
    ]
    result = generate_word_cloud(messages, top_n=10)
    assert len(result) > 0
    # Check that each item has word and frequency
    for item in result:
        assert item.word
        assert item.frequency >= 1


def test_word_cloud_generation_empty():
    """Test word cloud generation with empty messages."""
    result = generate_word_cloud([], top_n=10)
    assert result == []


def test_calculate_intimacy_basic():
    """Test intimacy calculation with basic input."""
    result = calculate_intimacy(
        sentiment_scores=[0.5, 0.6, 0.7],
        message_count=10,
        last_sender_id=2,
        current_user_id=1,
        consecutive_messages={1: 2, 2: 3}
    )
    assert 0 <= result.intimacy_score <= 100
    assert result.sentiment_factor >= 0
    assert result.frequency_factor >= 0
    assert result.flow_factor >= 0
    assert result.consecutive_factor >= 0


def test_calculate_intimacy_empty_sentiment():
    """Test intimacy calculation with empty sentiment scores."""
    result = calculate_intimacy(
        sentiment_scores=[],
        message_count=0,
        last_sender_id=1,
        current_user_id=1,
        consecutive_messages={}
    )
    assert result.intimacy_score >= 0


def test_word_cloud_api(client):
    """Test word cloud API endpoint."""
    response = client.post(
        "/api/v1/analysis/wordcloud",
        json={
            "messages": ["你好世界", "今天天气很好", "学习编程很有趣"],
            "top_n": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_intimacy_api(client):
    """Test intimacy calculation API endpoint."""
    response = client.post(
        "/api/v1/analysis/intimacy",
        json={
            "sentiment_scores": [0.5, 0.6, 0.7],
            "message_count": 100,
            "last_sender_id": 2,
            "current_user_id": 1,
            "consecutive_messages": {"1": 5, "2": 3}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "intimacy_score" in data
    assert 0 <= data["intimacy_score"] <= 100


def test_sentiment_api_without_api_key(client):
    """Test sentiment analysis API without API key configured."""
    response = client.post(
        "/api/v1/analysis/sentiment",
        json={
            "text": "今天天气真好，心情很愉快"
        }
    )
    # Should return 400 because DASHSCOPE_API_KEY is not configured
    assert response.status_code == 400
    assert "DASHSCOPE_API_KEY" in response.json()["detail"] or "dashscope" in response.json()["detail"]


def test_sentiment_api_with_mocked_response(client):
    """Test sentiment analysis API with mocked LLM response."""
    from backend.app.schemas.analysis import SentimentResult
    
    # Create a proper SentimentResult object
    mock_result = SentimentResult(
        sentiment_score=0.8,
        positive_score=0.7,
        negative_score=0.1,
        neutral_score=0.2
    )
    
    # Patch at the endpoint module level where the function is used
    with patch('backend.app.api.api_v1.endpoints.analysis.analyze_sentiment_llm', return_value=mock_result):
        response = client.post(
            "/api/v1/analysis/sentiment",
            json={
                "text": "今天天气真好，心情很愉快"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment_score"] == 0.8
        assert data["positive_score"] == 0.7


def test_calculate_intimacy_high_consecutive():
    """Test intimacy calculation with high consecutive messages (penalty case)."""
    result = calculate_intimacy(
        sentiment_scores=[0.5],
        message_count=50,
        last_sender_id=1,
        current_user_id=1,
        consecutive_messages={1: 15}  # High consecutive messages
    )
    # Should have low consecutive factor due to penalty
    assert result.consecutive_factor == 0.0
    assert 0 <= result.intimacy_score <= 100


def test_calculate_intimacy_other_last_sender():
    """Test intimacy calculation when other person sent last message."""
    result = calculate_intimacy(
        sentiment_scores=[0.5],
        message_count=10,
        last_sender_id=2,  # Other person sent last
        current_user_id=1,
        consecutive_messages={1: 2, 2: 3}
    )
    # Should have higher flow factor (20) because other person initiated
    assert result.flow_factor == 20.0


def test_word_cloud_with_stopwords():
    """Test that stopwords are properly filtered from word cloud."""
    messages = [
        "的的的是是是在在在了了了",  # All stopwords
        "今天天气很好"  # Contains some meaningful words
    ]
    result = generate_word_cloud(messages, top_n=10)
    # Should filter out stopwords and keep meaningful words
    word_list = [item.word for item in result]
    assert "的" not in word_list
    assert "是" not in word_list
    assert "在" not in word_list
