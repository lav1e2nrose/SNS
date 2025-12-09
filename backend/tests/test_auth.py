"""
Tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data


def test_register_duplicate_username(client, test_user):
    """Test registration with existing username."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",  # Already exists
            "email": "another@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_register_duplicate_email(client, test_user):
    """Test registration with existing email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "anotheruser",
            "email": "test@example.com",  # Already exists
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent",
            "password": "password123"
        }
    )
    assert response.status_code == 401


def test_register_and_login_with_long_password(client):
    """Test registration and login with password longer than 72 bytes."""
    # Password longer than bcrypt's 72-byte limit
    long_password = "a" * 100
    
    # Register with long password
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "longpassuser",
            "email": "longpass@example.com",
            "password": long_password,
            "full_name": "Long Password User"
        }
    )
    assert response.status_code == 201
    
    # Login with full long password should succeed
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "longpassuser",
            "password": long_password
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Login with truncated password (72 chars) should fail
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "longpassuser",
            "password": "a" * 72
        }
    )
    assert response.status_code == 401
