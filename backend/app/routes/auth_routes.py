from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from datetime import datetime

from app.database import get_db, users
from auth.jwt_manager import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from auth.decorators import get_current_user
import re

router = APIRouter(prefix="/api", tags=["auth"])


# =========================
# Validation email
# =========================

def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


# =========================
# Schemas Pydantic
# =========================

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: str
    password: str


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str


# =========================
# Register
# =========================

@router.post("/register/", response_model=AuthResponse, status_code=201)
def register(user: UserRegister):
    """
    Créer un nouvel utilisateur avec JWT tokens.
    """
    # Validate email format
    if not validate_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email invalide"
        )

    # Check if user already exists
    existing_user = users.find_one({
        "$or": [{"email": user.email}, {"username": user.username}]
    })

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'utilisateur ou l'email existe déjà"
        )

    try:
        # Create user document
        user_doc = {
            "username": user.username,
            "email": user.email,
            "hashed_password": hash_password(user.password),
            "created_at": datetime.utcnow()
        }

        result = users.insert_one(user_doc)
        user_id_str = str(result.inserted_id)

        # Generate tokens
        access_token = create_access_token({
            "user_id": user_id_str,
            "email": user.email,
            "username": user.username
        })
        
        refresh_token = create_refresh_token({
            "user_id": user_id_str
        })

        return {
            "user": {
                "id": user_id_str,
                "username": user.username,
                "email": user.email
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du compte"
        )


# =========================
# Login
# =========================

@router.post("/login/", response_model=TokenResponse)
def login(user: UserLogin):
    """
    Authentifier un utilisateur et retourner JWT tokens.
    """
    # Find user by email
    db_user = users.find_one({"email": user.email})

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    # Verify password
    try:
        if not verify_password(user.password, db_user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    user_id_str = str(db_user["_id"])

    # Generate tokens
    access_token = create_access_token({
        "user_id": user_id_str,
        "email": db_user["email"],
        "username": db_user["username"]
    })
    
    refresh_token = create_refresh_token({
        "user_id": user_id_str
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# =========================
# Refresh Token
# =========================

@router.post("/refresh/", response_model=TokenResponse)
def refresh(data: TokenRefresh):
    """
    Refresh expired access token using refresh token.
    """
    try:
        payload = decode_token(data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("user_id")
        
        # Get user to validate still exists
        try:
            db_user = users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            db_user = None

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
        user_id_str = str(db_user["_id"])

        # Generate new tokens
        access_token = create_access_token({
            "user_id": user_id_str,
            "email": db_user["email"],
            "username": db_user["username"]
        })
        
        refresh_token = create_refresh_token({
            "user_id": user_id_str
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# =========================
# Get Current User
# =========================

@router.get("/me/", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user profile.
    """
    try:
        user_id = ObjectId(current_user["user_id"])
        db_user = users.find_one({"_id": user_id})
    except Exception:
        db_user = None
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return {
        "id": str(db_user["_id"]),
        "username": db_user["username"],
        "email": db_user["email"]
    }


# =========================
# Logout (Optional)
# =========================

@router.post("/logout/")
def logout():
    """
    Logout endpoint (client should delete tokens).
    """
    return {
        "message": "Logout successful. Please delete your tokens."
    }


# =========================
# Test route
# =========================

@router.get("/users/")
def get_users():
    """
    Afficher les utilisateurs pour tester.
    """
    all_users = users.find()

    return [
        {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
        for user in all_users
    ]