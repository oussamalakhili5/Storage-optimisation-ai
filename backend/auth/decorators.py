"""
JWT Authentication Decorators and Middleware.

This module provides decorators and dependency injection helpers for:
- Protecting endpoints with token verification
- Extracting current user from token
- Token validation
"""

from functools import wraps
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthCredentials

from .jwt_manager import decode_token


# ========================
# Security Scheme
# ========================

security = HTTPBearer()


# ========================
# Dependency Injection
# ========================

def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> Dict:
    """
    FastAPI dependency to extract and validate the current user from JWT token.
    
    This function is used with FastAPI's dependency injection system.
    Use it in route parameters to automatically extract and validate tokens.
    
    Args:
        credentials (HTTPAuthCredentials): HTTP Bearer token from request headers
        
    Returns:
        Dict: Decoded token payload containing user information
        
    Raises:
        HTTPException: 
            - 401 if token is missing or invalid
            - 401 if token has expired
            
    Example:
        @app.get("/api/profile")
        def get_profile(current_user: Dict = Depends(get_current_user)):
            return {"user_id": current_user["user_id"], "email": current_user["email"]}
    """
    token = credentials.credentials
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id"
            )
        
        return payload
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_optional_user(request: Request) -> Optional[Dict]:
    """
    Extract current user from token if present, otherwise return None.
    
    Useful for endpoints that work both authenticated and unauthenticated.
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        Optional[Dict]: Decoded token payload if valid token present, None otherwise
        
    Example:
        @app.get("/api/posts")
        def get_posts(current_user: Optional[Dict] = Depends(get_optional_user)):
            if current_user:
                return {"posts": [...], "message": f"Hello {current_user['email']}"}
            else:
                return {"posts": [...], "message": "Hello guest"}
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    try:
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        return payload
    except Exception:
        return None


# ========================
# Decorator for Function-based Views
# ========================

def token_required(f):
    """
    Decorator to protect a route with JWT token verification.
    
    This decorator extracts the token from the Authorization header,
    validates it, and passes the decoded payload to the route function.
    
    Note: For FastAPI, using Depends(get_current_user) is preferred.
    This decorator is useful for other frameworks or custom use cases.
    
    Args:
        f: Route function to protect
        
    Returns:
        Wrapped function that requires valid JWT token
        
    Raises:
        HTTPException: 401 Unauthorized if token is missing or invalid
        
    Example:
        @app.get("/api/protected")
        @token_required
        def protected_route(current_user):
            return {"message": f"Hello {current_user['email']}"}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return jsonify({"detail": "Authorization header missing"}), 401
        
        try:
            # Format: "Bearer <token>"
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({"detail": "Invalid Authorization header format"}), 401
        
        try:
            payload = decode_token(token)
            # Pass user data to the route function
            kwargs["current_user"] = payload
            return f(*args, **kwargs)
            
        except ValueError as e:
            return jsonify({"detail": str(e)}), 401
        except Exception as e:
            return jsonify({"detail": "Invalid token"}), 401
    
    return decorated_function


# ========================
# Optional Token Decorator
# ========================

def token_optional(f):
    """
    Decorator for routes that work both authenticated and unauthenticated.
    
    If a valid token is provided, it's decoded and passed to the route.
    If no token is provided or it's invalid, the route still executes with None.
    
    Note: For FastAPI, using Depends(get_optional_user) is preferred.
    
    Args:
        f: Route function
        
    Returns:
        Wrapped function that accepts optional JWT token
        
    Example:
        @app.get("/api/posts")
        @token_optional
        def get_posts(current_user=None):
            if current_user:
                return {"posts": [...], "user": current_user["email"]}
            else:
                return {"posts": [...], "user": "anonymous"}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        
        auth_header = request.headers.get("Authorization")
        current_user = None
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
                current_user = decode_token(token)
            except Exception:
                # Token invalid or expired, but route still executes
                pass
        
        kwargs["current_user"] = current_user
        return f(*args, **kwargs)
    
    return decorated_function
