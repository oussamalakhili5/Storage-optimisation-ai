# JWT Authentication Documentation

## Overview

This project uses JWT (JSON Web Tokens) for secure, stateless authentication. The system includes:

- **Password Hashing**: bcrypt with 12 rounds
- **Token Generation**: HS256-signed JWT tokens
- **Access Tokens**: 15-minute expiration
- **Refresh Tokens**: 7-day expiration
- **Dependency Injection**: FastAPI-native authentication

---

## File Structure

```
backend/
├── auth/
│   ├── __init__.py              # Module initialization and exports
│   ├── jwt_manager.py           # Token generation, verification, password hashing
│   └── decorators.py            # FastAPI dependencies and decorators
├── main.py                       # Updated with JWT initialization
├── requirements.txt              # Updated with JWT dependencies
└── .env.example                  # Environment variables template
```

---

## Configuration

### 1. Create `.env` file

```bash
# Copy .env.example to .env
cp backend/.env.example backend/.env

# Edit .env and change SECRET_KEY to a secure value
SECRET_KEY=your-secret-key-generate-with-python-secrets
```

### 2. Generate a Secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output and paste it into `.env` as `SECRET_KEY`.**

### 3. Install Requirements

```bash
cd backend
pip install -r requirements.txt
```

---

## Usage Examples

### 1. Register a User

**Endpoint**: `POST /api/register/`

```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

**Response**:
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Login

**Endpoint**: `POST /api/login/`

```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Access Protected Endpoint

**Include Authorization header with Bearer token**:

```bash
curl -X GET http://localhost:8000/api/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Refresh Access Token

**Endpoint**: `POST /api/refresh/`

```bash
curl -X POST http://localhost:8000/api/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

---

## Implementation in Routes

### Using Dependency Injection (Recommended)

```python
from fastapi import APIRouter, Depends
from auth.decorators import get_current_user

router = APIRouter()

@router.get("/api/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Protected route - requires valid JWT token.
    
    current_user contains:
    - user_id
    - email
    - username
    - exp (expiration timestamp)
    """
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "message": f"Hello {current_user['email']}"
    }
```

### Optional Authentication

```python
from fastapi import Depends
from auth.decorators import get_optional_user

@router.get("/api/posts")
def get_posts(current_user: dict = Depends(get_optional_user)):
    """
    Route that works authenticated and unauthenticated.
    current_user is None if no valid token provided.
    """
    if current_user:
        return {"posts": [...], "user": current_user["email"]}
    else:
        return {"posts": [...], "user": None}
```

---

## API Reference

### `jwt_manager.py`

#### `hash_password(password: str) -> str`
Hashes a plaintext password using bcrypt.

```python
from auth.jwt_manager import hash_password

hashed = hash_password("MyPassword123")
# Returns: $2b$12$...
```

#### `verify_password(plain_password: str, hashed_password: str) -> bool`
Verifies a plaintext password against a hash.

```python
from auth.jwt_manager import verify_password

is_valid = verify_password("MyPassword123", hashed_password)
# Returns: True or False
```

#### `create_access_token(data: dict) -> str`
Generates a 15-minute access token.

```python
from auth.jwt_manager import create_access_token

token = create_access_token({
    "user_id": 1,
    "email": "user@example.com"
})
```

#### `create_refresh_token(data: dict) -> str`
Generates a 7-day refresh token.

```python
from auth.jwt_manager import create_refresh_token

token = create_refresh_token({"user_id": 1})
```

#### `decode_token(token: str) -> dict`
Decodes and validates a JWT token.

```python
from auth.jwt_manager import decode_token

payload = decode_token(token)
# Returns: {"user_id": 1, "email": "...", "exp": ...}
```

---

## Security Best Practices

### ✅ DO

- ✅ Store `SECRET_KEY` in `.env` file (never commit to Git)
- ✅ Use HTTPS in production
- ✅ Set strong `SECRET_KEY` (use `secrets` module)
- ✅ Use Bearer tokens in Authorization header
- ✅ Refresh access tokens regularly
- ✅ Validate token claims (user_id, exp, etc.)
- ✅ Use httpOnly cookies for tokens in production
- ✅ Implement rate limiting on login endpoint

### ❌ DON'T

- ❌ Store `SECRET_KEY` in code
- ❌ Use hardcoded credentials
- ❌ Store tokens in localStorage (use httpOnly cookies)
- ❌ Send tokens in URL or query parameters
- ❌ Skip token validation
- ❌ Use weak bcrypt rounds (< 10)
- ❌ Expose error details in responses
- ❌ Allow unlimited login attempts

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | N/A | **REQUIRED** - JWT signing key |
| `JWT_ALGORITHM` | HS256 | Token signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `BCRYPT_ROUNDS` | 12 | Password hashing strength |

---

## Troubleshooting

### "Invalid token" Error

**Cause**: Token has expired or is malformed

**Solution**: Request a new token using refresh token or login again

### "Authorization header missing" Error

**Cause**: No Authorization header provided

**Solution**: Include `Authorization: Bearer <token>` header

### "Invalid credentials" Error

**Cause**: Username/email or password incorrect

**Solution**: Check credentials and try again

### "Token has expired" Error

**Cause**: Access token older than 15 minutes

**Solution**: Use refresh token to get new access token

---

## Token Structure

JWT tokens have three parts: `header.payload.signature`

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload (Access Token)
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "type": "access",
  "exp": 1234567890
}
```

### Payload (Refresh Token)
```json
{
  "user_id": 1,
  "type": "refresh",
  "exp": 1234567890
}
```

---

## Testing

```python
import pytest
from auth.jwt_manager import (
    hash_password, verify_password,
    create_access_token, decode_token
)

def test_password_hashing():
    password = "SecurePass123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_token_generation():
    token = create_access_token({"user_id": 1, "email": "test@example.com"})
    payload = decode_token(token)
    
    assert payload["user_id"] == 1
    assert payload["email"] == "test@example.com"
```

---

## Support

For questions or issues, refer to:
- JWT: https://jwt.io
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- Bcrypt: https://github.com/pyca/bcrypt
