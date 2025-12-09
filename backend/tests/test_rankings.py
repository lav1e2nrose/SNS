"""
Tests for ranking endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.models.message import Message
from backend.app.models.friendship import Friendship
from backend.app.models.user import User
from backend.app.core.security import get_password_hash


def test_get_top_friends_empty(client, auth_headers, test_user):
    """Test getting top friends when no friends exist."""
    response = client.get(
        "/api/v1/rankings/top-friends",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_top_friends_with_data(client, auth_headers, test_user, test_user2, db_session):
    """Test getting top friends with friendship data."""
    # Create accepted friendship
    friendship = Friendship(
        user_id=test_user.id,
        friend_id=test_user2.id,
        status="accepted",
        intimacy_score=50.0,
        interaction_count=10,
        positive_interactions=8,
        negative_interactions=2
    )
    db_session.add(friendship)
    db_session.commit()
    
    response = client.get(
        "/api/v1/rankings/top-friends",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["friend_id"] == test_user2.id
    assert data[0]["intimacy_score"] == 50.0


def test_get_top_friends_ordered(client, auth_headers, test_user, db_session):
    """Test that top friends are ordered by intimacy score."""
    # Create additional test users
    user2 = User(
        username="friend1",
        email="friend1@example.com",
        hashed_password=get_password_hash("password"),
        full_name="Friend 1"
    )
    user3 = User(
        username="friend2",
        email="friend2@example.com",
        hashed_password=get_password_hash("password"),
        full_name="Friend 2"
    )
    db_session.add(user2)
    db_session.add(user3)
    db_session.commit()
    db_session.refresh(user2)
    db_session.refresh(user3)
    
    # Create friendships with different intimacy scores
    friendship1 = Friendship(
        user_id=test_user.id,
        friend_id=user2.id,
        status="accepted",
        intimacy_score=30.0,
        interaction_count=5,
        positive_interactions=3,
        negative_interactions=2
    )
    friendship2 = Friendship(
        user_id=test_user.id,
        friend_id=user3.id,
        status="accepted",
        intimacy_score=70.0,
        interaction_count=15,
        positive_interactions=12,
        negative_interactions=3
    )
    db_session.add(friendship1)
    db_session.add(friendship2)
    db_session.commit()
    
    response = client.get(
        "/api/v1/rankings/top-friends",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Higher intimacy score should be first
    assert data[0]["intimacy_score"] == 70.0
    assert data[1]["intimacy_score"] == 30.0


def test_get_top_friends_limit(client, auth_headers, test_user, db_session):
    """Test limiting the number of top friends returned."""
    # Create multiple friends
    for i in range(5):
        user = User(
            username=f"limitfriend{i}",
            email=f"limitfriend{i}@example.com",
            hashed_password=get_password_hash("password"),
            full_name=f"Limit Friend {i}"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        friendship = Friendship(
            user_id=test_user.id,
            friend_id=user.id,
            status="accepted",
            intimacy_score=float(i * 10),
            interaction_count=i,
            positive_interactions=i,
            negative_interactions=0
        )
        db_session.add(friendship)
    db_session.commit()
    
    response = client.get(
        "/api/v1/rankings/top-friends?limit=3",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
