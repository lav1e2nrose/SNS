"""
Tests for chat endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.models.message import Message


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
