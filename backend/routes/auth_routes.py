"""
Authentication Routes - Production Ready

This module provides complete authentication endpoints with:
- User registration with validation
- User login with JWT generation
- Protected user profile endpoint
- Logout functionality
- Proper error handling and security considerations
"""

import re
from typing import Optional, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from auth.jwt_manager import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from auth.decorators import get_current_user


# ========================
# Router Setup
# ========================

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Unauthorized"},
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


# ========================
# Request/Response Models
# ========================

class PasswordValidator(BaseModel):
    """Base model with password validation."""
    
    @validator("password")
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength.
        
        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        
        Args:
            v: Password string
            
        Returns:
            str: Validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not v or len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        return v


class RegisterRequest(PasswordValidator):
    """User registration request model."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        regex="^[a-zA-Z0-9_-]+$",
        description="Username (alphanumeric, underscore, hyphen only)"
    )
    email: str = Field(
        ...,
        max_length=100,
        description="User email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 chars, mixed case + numbers)"
    )
    
    @validator("email")
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()
    
    @validator("username")
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be 3-50 characters")
        if not re.match("^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscore, hyphen")
        return v


class LoginRequest(BaseModel):
    """User login request model."""
    
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    @validator("email")
    def validate_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower()


class UserResponse(BaseModel):
    """User profile response model."""
    
    id: int
    username: str
    email: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response model."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


class LoginResponse(BaseModel):
    """Login response model."""
    
    access_token: str
    refresh_token: str
    token_type: str


class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str


# ========================
# Helper Functions
# ========================

def get_db():
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def format_error_response(detail: str, status_code: int) -> HTTPException:
    """
    Format error response with proper HTTP exception.
    
    Args:
        detail: Error message
        status_code: HTTP status code
        
    Returns:
        HTTPException: Formatted exception
    """
    return HTTPException(
        status_code=status_code,
        detail=detail,
    )


def sanitize_input(text: str, max_length: int = 100) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    return text


# ========================
# Registration Endpoint
# ========================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account and return authentication tokens"
)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Register a new user with email and password.
    
    **Validation Requirements:**
    - Username: 3-50 characters, alphanumeric + underscore/hyphen
    - Email: Valid email format (RFC 5322)
    - Password: 
      - Minimum 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
    
    **Security Notes:**
    - Passwords are hashed with bcrypt (12 rounds)
    - Tokens are JWT-signed with HS256
    - No specific error messages for enumeration prevention
    
    **Example:**
    ```json
    {
      "username": "john_doe",
      "email": "john@example.com",
      "password": "SecurePass123"
    }
    ```
    
    Args:
        user_data: Registration data
        db: Database session
        
    Returns:
        TokenResponse: User data + access/refresh tokens
        
    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 409 for duplicate user
        HTTPException: 500 for server errors
    """
    
    try:
        # Sanitize inputs
        username = sanitize_input(user_data.username, 50)
        email = sanitize_input(user_data.email, 100).lower()
        password = user_data.password  # Don't sanitize passwords
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            # Security: Don't reveal which field caused conflict
            raise format_error_response(
                detail="Registration failed. Please try again.",
                status_code=status.HTTP_409_CONFLICT
            )
        
        # Hash password
        try:
            hashed_password = hash_password(password)
        except ValueError as e:
            raise format_error_response(
                detail="Password hashing failed. Please try again.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate tokens
        access_token = create_access_token({
            "user_id": new_user.id,
            "email": new_user.email,
            "username": new_user.username
        })
        
        refresh_token = create_refresh_token({
            "user_id": new_user.id
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(new_user)
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise format_error_response(
            detail="Invalid input data. Please try again.",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        db.rollback()
        raise format_error_response(
            detail="Registration failed. Please try again later.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========================
# Login Endpoint
# ========================

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate user with email and password, return JWT tokens"
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Authenticate user and generate JWT tokens.
    
    **Security Notes:**
    - Returns generic error message to prevent user enumeration
    - Passwords are verified using bcrypt
    - Tokens expire after configured time periods
    
    **Example:**
    ```json
    {
      "email": "john@example.com",
      "password": "SecurePass123"
    }
    ```
    
    Args:
        credentials: Login credentials
        db: Database session
        
    Returns:
        LoginResponse: Access and refresh tokens
        
    Raises:
        HTTPException: 401 for invalid credentials
        HTTPException: 500 for server errors
    """
    
    try:
        email = sanitize_input(credentials.email, 100).lower()
        password = credentials.password
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        # Security: Same error message for both user not found and wrong password
        if not user:
            raise format_error_response(
                detail="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify password
        try:
            is_valid = verify_password(password, user.hashed_password)
        except Exception:
            is_valid = False
        
        if not is_valid:
            # Security: Same error message as user not found
            raise format_error_response(
                detail="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate tokens
        access_token = create_access_token({
            "user_id": user.id,
            "email": user.email,
            "username": user.username
        })
        
        refresh_token = create_refresh_token({
            "user_id": user.id
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise format_error_response(
            detail="Login failed. Please try again later.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========================
# Protected User Profile Endpoint
# ========================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve authenticated user's profile information"
)
def get_profile(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get current authenticated user's profile.
    
    **Security:** Requires valid JWT token in Authorization header.
    
    **Example Request:**
    ```
    GET /api/auth/me
    Authorization: Bearer <your_access_token>
    ```
    
    **Example Response:**
    ```json
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "created_at": "2026-06-17T12:34:56"
    }
    ```
    
    Args:
        current_user: Current user from JWT token (injected)
        db: Database session
        
    Returns:
        UserResponse: User profile data
        
    Raises:
        HTTPException: 401 if token invalid or expired
        HTTPException: 404 if user not found
    """
    
    try:
        user_id = current_user.get("user_id")
        
        if not user_id:
            raise format_error_response(
                detail="Invalid token",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise format_error_response(
                detail="User not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise format_error_response(
            detail="Failed to retrieve user profile",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========================
# Logout Endpoint
# ========================

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout current user (client-side token deletion)"
)
def logout(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Logout endpoint for authenticated users.
    
    **Security Notes:**
    - In JWT-based authentication, logout is primarily client-side
    - This endpoint confirms logout request
    - Client should delete stored tokens
    - For server-side logout, implement token blacklist
    
    **Example Request:**
    ```
    POST /api/auth/logout
    Authorization: Bearer <your_access_token>
    ```
    
    Args:
        current_user: Current user from JWT token (injected)
        
    Returns:
        MessageResponse: Confirmation message
    """
    
    return {
        "message": "Logout successful. Please delete your tokens from client."
    }


# ========================
# Health Check Endpoint
# ========================

@router.get(
    "/health",
    response_model=MessageResponse,
    summary="Authentication service health check",
    description="Check if authentication service is available"
)
def health_check() -> Dict:
    """
    Simple health check endpoint for monitoring.
    
    Returns:
        Dict: Service status message
    """
    return {
        "message": "Authentication service is healthy"
    }
