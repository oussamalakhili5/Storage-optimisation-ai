from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
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
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


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
# Connexion DB
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# Register
# =========================

@router.post("/register/", response_model=AuthResponse, status_code=201)
def register(user: UserRegister, db: Session = Depends(get_db)):
    """
    Créer un nouvel utilisateur avec JWT tokens.
    
    Args:
        user: Registration data (username, email, password)
        db: Database session
        
    Returns:
        AuthResponse: User data + access and refresh tokens
        
    Raises:
        HTTPException: 400 for invalid email or duplicate user
        HTTPException: 500 for server errors
    """
    
    # Validate email format
    if not validate_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email invalide"
        )

    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'utilisateur ou l'email existe déjà"
        )

    try:
        # Hash password and create user
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.password)
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Generate tokens
        access_token = create_access_token({
            "user_id": db_user.id,
            "email": db_user.email,
            "username": db_user.username
        })
        
        refresh_token = create_refresh_token({
            "user_id": db_user.id
        })

        return {
            "user": UserResponse.from_orm(db_user),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du compte"
        )


# =========================
# Login
# =========================

@router.post("/login/", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Authentifier un utilisateur et retourner JWT tokens.
    
    Args:
        user: Login credentials (email, password)
        db: Database session
        
    Returns:
        TokenResponse: Access and refresh tokens
        
    Raises:
        HTTPException: 401 for invalid credentials
    """
    
    # Find user by email
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    # Verify password
    try:
        if not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    # Generate tokens
    access_token = create_access_token({
        "user_id": db_user.id,
        "email": db_user.email,
        "username": db_user.username
    })
    
    refresh_token = create_refresh_token({
        "user_id": db_user.id
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
def refresh(data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh expired access token using refresh token.
    
    Args:
        data: Refresh token
        db: Database session
        
    Returns:
        TokenResponse: New access and refresh tokens
        
    Raises:
        HTTPException: 401 if refresh token is invalid
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
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
        # Generate new tokens
        access_token = create_access_token({
            "user_id": db_user.id,
            "email": db_user.email,
            "username": db_user.username
        })
        
        refresh_token = create_refresh_token({
            "user_id": db_user.id
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
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get current authenticated user profile.
    
    Args:
        current_user: Current user from JWT token (via dependency)
        db: Database session
        
    Returns:
        UserResponse: User profile data
        
    Raises:
        HTTPException: 404 if user not found
    """
    
    db_user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return UserResponse.from_orm(db_user)


# =========================
# Logout (Optional - for client-side cleanup)
# =========================

@router.post("/logout/")
def logout():
    """
    Logout endpoint (client should delete tokens).
    
    In JWT-based auth, logout is typically client-side (delete tokens).
    This endpoint can be used to:
    - Log the logout event
    - Blacklist tokens (requires token blacklist database)
    - Update user status
    
    Returns:
        Dict: Logout confirmation message
    """
    return {
        "message": "Logout successful. Please delete your tokens."
    }


# =========================
# Test route
# =========================

@router.get("/users/")
def get_users(db: Session = Depends(get_db)):
    """
    Afficher les utilisateurs pour tester.
    """

    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
        for user in users
    ]