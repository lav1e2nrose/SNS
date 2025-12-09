"""
Tests for analysis endpoints and services.
"""
import pytest
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
