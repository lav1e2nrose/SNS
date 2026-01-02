"""
Tests for chat endpoints.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.app.models.message import Message
from backend.app.schemas.analysis import SentimentResult


def test_get_chat_history_empty(client, auth_headers, test_user, test_user2):
    """Test getting empty chat history."""
    response = client.get(
        f"/api/v1/chat/{test_user2.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_chat_history_nonexistent_friend(client, auth_headers):
    """Test getting chat history with non-existent user."""
    response = client.get(
        "/api/v1/chat/99999",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_get_chat_history_with_messages(client, auth_headers, test_user, test_user2, db_session):
    """Test getting chat history with messages."""
    # Add some messages directly to the database
    msg1 = Message(
        sender_id=test_user.id,
        receiver_id=test_user2.id,
        content="Hello!",
        is_read=False,
        sentiment_score=0.5
    )
    msg2 = Message(
        sender_id=test_user2.id,
        receiver_id=test_user.id,
        content="Hi there!",
        is_read=False,
        sentiment_score=0.6
    )
    db_session.add(msg1)
    db_session.add(msg2)
    db_session.commit()
    
    response = client.get(
        f"/api/v1/chat/{test_user2.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_mark_messages_as_read(client, auth_headers, test_user, test_user2, db_session):
    """Test marking messages as read."""
    # Add unread messages from user2 to user1
    msg = Message(
        sender_id=test_user2.id,
        receiver_id=test_user.id,
        content="Hello!",
        is_read=False,
        sentiment_score=0.0
    )
    db_session.add(msg)
    db_session.commit()
    
    # Mark as read
    response = client.put(
        f"/api/v1/chat/{test_user2.id}/read",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["marked_as_read"] == 1


def test_get_unread_count(client, auth_headers, test_user, test_user2, db_session):
    """Test getting unread message count."""
    # Add unread messages from user2 to user1
    for i in range(3):
        msg = Message(
            sender_id=test_user2.id,
            receiver_id=test_user.id,
            content=f"Message {i}",
            is_read=False,
            sentiment_score=0.0
        )
        db_session.add(msg)
    db_session.commit()
    
    response = client.get(
        f"/api/v1/chat/{test_user2.id}/unread",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["unread_count"] == 3


def test_unread_count_nonexistent_friend(client, auth_headers):
    """Test getting unread count for non-existent user."""
    response = client.get(
        "/api/v1/chat/99999/unread",
        headers=auth_headers
    )
    assert response.status_code == 404


def test_websocket_chat(client, auth_token, test_user, test_user2, db_session):
    """Test WebSocket chat functionality."""
    # Connect to WebSocket with token
    with client.websocket_connect(
        f"/api/v1/ws/{test_user2.id}?token={auth_token}"
    ) as websocket:
        # Send a message
        message_content = "Hello via WebSocket!"
        websocket.send_text(json.dumps({"content": message_content}))
        
        # Receive echo response
        data = websocket.receive_text()
        response = json.loads(data)
        
        assert response["content"] == message_content
        assert response["sender_id"] == test_user.id
        assert response["receiver_id"] == test_user2.id
        assert response["is_read"] == False


def test_websocket_chat_invalid_token(client, test_user2):
    """Test WebSocket connection with invalid token."""
    # This should fail to connect or close immediately
    try:
        with client.websocket_connect(
            f"/api/v1/ws/{test_user2.id}?token=invalid_token"
        ) as websocket:
            # If connection succeeds but token is invalid, 
            # we should not be able to receive any normal response
            pytest.fail("Should not connect with invalid token")
    except Exception:
        # Expected: connection should fail or be rejected
        pass


def test_websocket_chat_nonexistent_friend(client, auth_token, test_user):
    """Test WebSocket connection to non-existent friend."""
    try:
        with client.websocket_connect(
            f"/api/v1/ws/99999?token={auth_token}"
        ) as websocket:
            # Should close immediately
            pytest.fail("Should not connect to non-existent friend")
    except Exception:
        # Expected: connection should fail
        pass


@patch('backend.app.api.api_v1.endpoints.chat.analyze_sentiment_llm')
def test_websocket_chat_with_sentiment_analysis(mock_sentiment, client, auth_token, test_user, test_user2, db_session):
    """Test WebSocket chat with sentiment analysis integration."""
    # Mock the sentiment analysis to return predictable values
    mock_sentiment_result = SentimentResult(
        sentiment_score=0.8,
        positive_score=0.85,
        negative_score=0.05,
        neutral_score=0.10
    )
    mock_sentiment.return_value = mock_sentiment_result
    
    # Connect to WebSocket with token
    with client.websocket_connect(
        f"/api/v1/ws/{test_user2.id}?token={auth_token}"
    ) as websocket:
        # Send a message
        message_content = "I'm so happy today!"
        websocket.send_text(json.dumps({"content": message_content}))
        
        # Receive echo response
        data = websocket.receive_text()
        response = json.loads(data)
        
        # Verify basic message fields
        assert response["content"] == message_content
        assert response["sender_id"] == test_user.id
        assert response["receiver_id"] == test_user2.id
        assert response["is_read"] == False
        
        # Verify sentiment fields are included in response
        assert "sentiment_score" in response
        assert "positive_score" in response
        assert "negative_score" in response
        assert "neutral_score" in response
        
        # Verify sentiment values match the mocked analysis
        assert response["sentiment_score"] == 0.8
        assert response["positive_score"] == 0.85
        assert response["negative_score"] == 0.05
        assert response["neutral_score"] == 0.10
        
        # Verify sentiment analysis was called
        mock_sentiment.assert_called_once_with(message_content)
        
        # Verify message is persisted in database with sentiment scores
        saved_message = db_session.query(Message).filter(
            Message.content == message_content
        ).first()
        assert saved_message is not None
        assert saved_message.sentiment_score == 0.8
        assert saved_message.positive_score == 0.85
        assert saved_message.negative_score == 0.05
        assert saved_message.neutral_score == 0.10


@patch('backend.app.api.api_v1.endpoints.chat.analyze_sentiment_llm')
def test_websocket_chat_sentiment_analysis_failure(mock_sentiment, client, auth_token, test_user, test_user2, db_session):
    """Test WebSocket chat when sentiment analysis fails gracefully."""
    # Mock sentiment analysis to raise an exception (could be any error)
    mock_sentiment.side_effect = ValueError("API configuration error")
    
    # Connect to WebSocket with token
    with client.websocket_connect(
        f"/api/v1/ws/{test_user2.id}?token={auth_token}"
    ) as websocket:
        # Send a message
        message_content = "Hello, how are you?"
        websocket.send_text(json.dumps({"content": message_content}))
        
        # Receive echo response - chat should still work
        data = websocket.receive_text()
        response = json.loads(data)
        
        # Verify basic message fields still work
        assert response["content"] == message_content
        assert response["sender_id"] == test_user.id
        assert response["receiver_id"] == test_user2.id
        
        # Verify sentiment fields are None when analysis fails
        assert response["sentiment_score"] is None
        assert response["positive_score"] is None
        assert response["negative_score"] is None
        assert response["neutral_score"] is None
        
        # Verify message is still persisted even when sentiment analysis fails
        saved_message = db_session.query(Message).filter(
            Message.content == message_content
        ).first()
        assert saved_message is not None
        assert saved_message.sentiment_score is None
