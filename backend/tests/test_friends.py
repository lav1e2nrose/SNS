"""
Tests for friendship management endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_add_friend(client, auth_headers, test_user, test_user2):
    """Test adding a friend."""
    response = client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user2.id},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["friend_id"] == test_user2.id
    assert data["status"] == "pending"


def test_add_self_as_friend(client, auth_headers, test_user):
    """Test that adding yourself as friend fails."""
    response = client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user.id},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "Cannot add yourself" in response.json()["detail"]


def test_add_nonexistent_friend(client, auth_headers):
    """Test adding a non-existent user as friend."""
    response = client.post(
        "/api/v1/friends/",
        json={"friend_id": 99999},
        headers=auth_headers
    )
    assert response.status_code == 404


def test_add_duplicate_friend(client, auth_headers, test_user, test_user2):
    """Test adding the same friend twice."""
    # First request
    client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user2.id},
        headers=auth_headers
    )
    # Second request should fail
    response = client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user2.id},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_friends(client, auth_headers, test_user, test_user2):
    """Test getting friends list."""
    # Add a friend first
    client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user2.id},
        headers=auth_headers
    )
    
    response = client.get("/api/v1/friends/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_user2.id
    assert data[0]["username"] == test_user2.username


def test_update_friendship_status(client, auth_headers, test_user, test_user2):
    """Test accepting a friend request."""
    # Add a friend first
    client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user2.id},
        headers=auth_headers
    )
    
    # Accept the friendship
    response = client.put(
        f"/api/v1/friends/{test_user2.id}",
        json={"status": "accepted"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"


def test_remove_friend(client, auth_headers, test_user, test_user2):
    """Test removing a friend."""
    # Add a friend first
    client.post(
        "/api/v1/friends/",
        json={"friend_id": test_user2.id},
        headers=auth_headers
    )
    
    # Remove the friend
    response = client.delete(
        f"/api/v1/friends/{test_user2.id}",
        headers=auth_headers
    )
    assert response.status_code == 204
    
    # Verify friend is removed
    response = client.get("/api/v1/friends/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_remove_nonexistent_friend(client, auth_headers):
    """Test removing a friend that doesn't exist."""
    response = client.delete(
        "/api/v1/friends/99999",
        headers=auth_headers
    )
    assert response.status_code == 404
