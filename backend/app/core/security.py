"""
Security utilities for JWT token handling and password hashing.
"""
import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from backend.app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prehash_password(password: str) -> str:
    """
    Pre-hash password with SHA-256 to handle passwords longer than 72 bytes.
    
    Bcrypt has a 72-byte limit for passwords. This function hashes the password
    with SHA-256 first, then base64 encodes it to create a fixed-length input
    that bcrypt can handle regardless of the original password length.
    
    Args:
        password: Plain text password
        
    Returns:
        Base64-encoded SHA-256 hash of the password
    """
    sha256_hash = hashlib.sha256(password.encode('utf-8')).digest()
    return base64.b64encode(sha256_hash).decode('ascii')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    prehashed = _prehash_password(plain_password)
    return pwd_context.verify(prehashed, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    prehashed = _prehash_password(password)
    return pwd_context.hash(prehashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
