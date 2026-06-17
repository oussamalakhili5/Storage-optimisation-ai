from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import SessionLocal
from app.models.user import User
import re

router = APIRouter(prefix="/api", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


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
# Password utils
# =========================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# =========================
# Register
# =========================

@router.post("/register/", response_model=UserResponse, status_code=201)
def register(user: UserRegister, db: Session = Depends(get_db)):
    """
    Créer un nouvel utilisateur.
    """

    if not validate_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email invalide"
        )

    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'utilisateur existe déjà"
        )

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )


# =========================
# Login
# =========================

@router.post("/login/")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Connecter un utilisateur avec email et password.
    """

    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    return {
        "message": "Connexion réussie",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email
        }
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