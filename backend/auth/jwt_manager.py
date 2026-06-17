"""
JWT Token Management and Password Hashing.

This module handles:
- JWT token initialization with FastAPI/Flask
- Password hashing with bcrypt
- Token generation (access & refresh tokens)
- Password verification
"""

import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from functools import wraps


# ========================
# Configuration
# ========================

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))


# ========================
# JWT Initialization
# ========================

def init_jwt(app):
    """
    Initialize JWT with FastAPI application.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        None
    """
    # For FastAPI, JWT is typically initialized via middleware
    # This is a placeholder for potential additional setup
    app.state.jwt_secret_key = SECRET_KEY
    app.state.jwt_algorithm = ALGORITHM
    return None


# ========================
# Password Hashing & Verification
# ========================

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    
    Args:
        password (str): Plaintext password to hash
        
    Returns:
        str: Hashed password (includes salt and hash)
        
    Raises:
        ValueError: If password is empty or invalid
        
    Example:
        >>> hashed = hash_password("SecurePass123")
        >>> len(hashed) > 50  # Bcrypt hashes are ~60 chars
        True
    """
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    
    try:
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Error hashing password: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.
    
    Args:
        plain_password (str): Plaintext password to verify
        hashed_password (str): Hashed password from database
        
    Returns:
        bool: True if passwords match, False otherwise
        
    Raises:
        ValueError: If inputs are invalid
        
    Example:
        >>> hashed = hash_password("MyPass123")
        >>> verify_password("MyPass123", hashed)
        True
        >>> verify_password("WrongPass", hashed)
        False
    """
    if not plain_password or not hashed_password:
        return False
    
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        raise ValueError(f"Error verifying password: {str(e)}")


# ========================
# Token Generation
# ========================

def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data (Dict): Payload data to encode (usually contains user_id, email, etc.)
        expires_delta (timedelta, optional): Token expiration time. 
                                            Defaults to ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        str: Encoded JWT token
        
    Raises:
        ValueError: If data is empty or encoding fails
        
    Example:
        >>> token = create_access_token({"user_id": 1, "email": "user@example.com"})
        >>> len(token) > 100
        True
    """
    if not data:
        raise ValueError("Token data cannot be empty")
    
    try:
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        return encoded_jwt
        
    except Exception as e:
        raise ValueError(f"Error creating access token: {str(e)}")


def create_refresh_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token (long-lived).
    
    Args:
        data (Dict): Payload data (usually contains user_id)
        expires_delta (timedelta, optional): Token expiration time.
                                            Defaults to REFRESH_TOKEN_EXPIRE_DAYS
        
    Returns:
        str: Encoded JWT refresh token
        
    Raises:
        ValueError: If data is empty or encoding fails
        
    Example:
        >>> token = create_refresh_token({"user_id": 1})
        >>> len(token) > 100
        True
    """
    if not data:
        raise ValueError("Token data cannot be empty")
    
    try:
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        return encoded_jwt
        
    except Exception as e:
        raise ValueError(f"Error creating refresh token: {str(e)}")


# ========================
# Token Decoding
# ========================

def decode_token(token: str) -> Dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token (str): JWT token to decode
        
    Returns:
        Dict: Decoded token payload
        
    Raises:
        jwt.InvalidTokenError: If token is invalid, expired, or tampered
        
    Example:
        >>> token = create_access_token({"user_id": 1})
        >>> payload = decode_token(token)
        >>> payload["user_id"]
        1
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
