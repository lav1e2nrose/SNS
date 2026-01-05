"""
Integration tests for complete chat flow.
"""
import pytest
import json
from fastapi.testclient import TestClient
from backend.app.models.message import Message
from backend.app.models.friendship import Friendship


def test_complete_chat_flow(client, auth_headers, auth_token, test_user, test_user2, db_session):
    """Test complete chat flow: add friend, chat, analyze."""
    # Step 1: Add friend
    response = client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user2.id},
        headers=auth_headers
    )
    assert response.status_code == 201
    
    # Step 2: Accept friendship
    response = client.put(
        f"/api/v1/friends/{test_user2.id}",
        json={"status": "accepted"},
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Step 3: Send messages via WebSocket
    with client.websocket_connect(
        f"/api/v1/ws/{test_user2.id}?token={auth_token}"
    ) as websocket:
        # Send multiple messages
        messages = ["你好！", "今天天气真好", "很高兴认识你"]
        for content in messages:
            websocket.send_text(json.dumps({"content": content}))
            response = websocket.receive_text()
            data = json.loads(response)
            assert data["content"] == content
    
    # Step 4: Verify chat history
    response = client.get(
        f"/api/v1/chat/{test_user2.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 3
    
    # Step 5: Generate word cloud
    response = client.post(
        "/api/v1/analysis/wordcloud",
        json={
            "messages": [msg["content"] for msg in history],
            "top_n": 10
        }
    )
    assert response.status_code == 200
    word_cloud = response.json()
    assert isinstance(word_cloud, list)
    
    # Step 6: Calculate intimacy
    response = client.post(
        "/api/v1/analysis/intimacy",
        json={
            "sentiment_scores": [0.5, 0.6, 0.7],
            "message_count": len(history),
            "last_sender_id": test_user.id,
            "current_user_id": test_user.id,
            "consecutive_messages": {str(test_user.id): 3}
        }
    )
    assert response.status_code == 200
    intimacy = response.json()
    assert "intimacy_score" in intimacy
    
    # Step 7: Check rankings
    response = client.get(
        "/api/v1/rankings/top-friends",
        headers=auth_headers
    )
    assert response.status_code == 200
    rankings = response.json()
    assert len(rankings) == 1
    assert rankings[0]["friend_id"] == test_user2.id


def test_friendship_interaction_count_updates(client, auth_headers, auth_token, test_user, test_user2, db_session):
    """Test that friendship interaction count is updated after chat."""
    # Add and accept friend
    client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user2.id},
        headers=auth_headers
    )
    client.put(
        f"/api/v1/friends/{test_user2.id}",
        json={"status": "accepted"},
        headers=auth_headers
    )
    
    # Get initial friendship state
    friendship = db_session.query(Friendship).filter(
        Friendship.user_id == test_user.id,
        Friendship.friend_id == test_user2.id
    ).first()
    initial_count = friendship.interaction_count or 0
    
    # Send messages via WebSocket
    with client.websocket_connect(
        f"/api/v1/ws/{test_user2.id}?token={auth_token}"
    ) as websocket:
        websocket.send_text(json.dumps({"content": "Test message 1"}))
        websocket.receive_text()
        websocket.send_text(json.dumps({"content": "Test message 2"}))
        websocket.receive_text()
    
    # Refresh session to get updated data
    db_session.expire_all()
    friendship = db_session.query(Friendship).filter(
        Friendship.user_id == test_user.id,
        Friendship.friend_id == test_user2.id
    ).first()
    
    # Verify interaction count increased
    assert friendship.interaction_count == initial_count + 2
    assert friendship.intimacy_score is not None
    assert friendship.intimacy_score > 0


def test_unread_messages_flow(client, auth_headers, test_user, test_user2, db_session):
    """Test unread message count and marking as read."""
    # Add messages from user2 to user1
    for i in range(5):
        msg = Message(
            sender_id=test_user2.id,
            receiver_id=test_user.id,
            content=f"Message {i}",
            is_read=False,
            sentiment_score=0.0
        )
        db_session.add(msg)
    db_session.commit()
    
    # Check unread count
    response = client.get(
        f"/api/v1/chat/{test_user2.id}/unread",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["unread_count"] == 5
    
    # Mark as read
    response = client.put(
        f"/api/v1/chat/{test_user2.id}/read",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["marked_as_read"] == 5
    
    # Verify unread count is now 0
    response = client.get(
        f"/api/v1/chat/{test_user2.id}/unread",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["unread_count"] == 0
