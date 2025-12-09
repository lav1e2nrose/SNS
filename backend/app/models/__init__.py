"""Data models module."""
from backend.app.models.user import User
from backend.app.models.message import Message
from backend.app.models.friendship import Friendship

__all__ = ["User", "Message", "Friendship"]
