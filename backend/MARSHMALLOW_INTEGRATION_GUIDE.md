# Auth Routes Integration Example - Using Marshmallow Validators

## Example: Updated Registration Route with Validator Decorator

Below is an example of how to update the `backend/routes/auth_routes.py` to use the new Marshmallow validation decorator:

### Before (Current Implementation with Pydantic)
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    
    @validator("email")
    def validate_email(cls, v):
        # manual validation
        return v

@router.post("/register")
async def register(request: RegisterRequest):
    # Pydantic handles validation automatically
    try:
        user = create_user(request.dict())
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### After (Using Marshmallow Validator Decorator)
```python
from fastapi import APIRouter, HTTPException, Request, status
from schemas.auth_schemas import UserRegisterSchema, TokenResponseSchema
from utils.validators import validate_request
from auth.jwt_manager import hash_password, create_access_token, create_refresh_token

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Invalid input data"},
        409: {"description": "User already exists"},
    }
)
@validate_request(UserRegisterSchema)
async def register(request: Request, validated_data: dict):
    """
    Register a new user with email and password.
    
    The @validate_request decorator:
    1. Extracts JSON from request body
    2. Validates against UserRegisterSchema
    3. Deserializes and cleans the data
    4. Passes validated_data to the route handler
    
    Args:
        request: FastAPI Request object
        validated_data: Dictionary with validated user data:
            - username: str (3-50 chars, validated format)
            - email: str (valid RFC 5322 format, lowercased)
            - password: str (8+ chars, uppercase, lowercase, digits)
    
    Returns:
        dict: User and tokens response
        
    Raises:
        HTTPException: 422 if validation fails
        HTTPException: 409 if email already exists
    """
    
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == validated_data['email']) | 
            (User.username == validated_data['username'])
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email or username already exists"
            )
        
        # Hash password
        hashed_password = hash_password(validated_data['password'])
        
        # Create new user
        new_user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate tokens
        access_token = create_access_token({"sub": str(new_user.id)})
        refresh_token = create_refresh_token({"sub": str(new_user.id)})
        
        # Return response with tokens
        return {
            "status": "success",
            "message": "User registered successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 15,  # minutes
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "created_at": new_user.created_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    finally:
        db.close()
```

## Key Differences

### 1. Validation Handling
**Pydantic (Current):**
```python
class RegisterRequest(BaseModel):
    password: str = Field(..., min_length=8)
    
    @validator("password")
    def validate_password(cls, v):
        # Inline validation
        return v
```

**Marshmallow (New):**
```python
@validate_request(UserRegisterSchema)
async def register(request: Request, validated_data: dict):
    # validated_data already contains fully validated data
```

### 2. Error Responses
**Pydantic (Current) - Returns 422:**
```json
{
    "detail": [
        {
            "loc": ["body", "email"],
            "msg": "invalid email format",
            "type": "value_error.email"
        }
    ]
}
```

**Marshmallow (New) - More descriptive:**
```json
{
    "detail": {
        "status": "validation_error",
        "errors": {
            "email": ["Invalid email format"],
            "password": ["Password must be at least 8 characters long"]
        }
    }
}
```

### 3. Code Organization
**Before:** Validation logic scattered in routes  
**After:** Centralized in `schemas/` directory

## Example: Login Route

```python
from schemas.auth_schemas import UserLoginSchema

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="User login",
)
@validate_request(UserLoginSchema)
async def login(request: Request, validated_data: dict):
    """
    Authenticate user and return tokens.
    
    The decorator validates:
    - email: Valid RFC 5322 format
    - password: Required, non-empty
    
    Args:
        validated_data: {
            "email": str (lowercased),
            "password": str
        }
    
    Returns:
        dict: Tokens and user info
    """
    
    db = SessionLocal()
    try:
        # Find user by email
        user = db.query(User).filter(User.email == validated_data['email']).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(validated_data['password'], user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 15,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }
    
    finally:
        db.close()
```

## Benefits of This Approach

✅ **Separation of Concerns**
- Validation logic in `schemas/`
- Routes focus on business logic
- Easy to reuse schemas

✅ **Consistent Validation**
- All requests validated the same way
- Central place to update rules
- No validation logic duplication

✅ **Better Error Messages**
- Descriptive validation errors
- Clear field-level error details
- Structured JSON responses

✅ **Type Safety**
- Marshmallow provides type hints
- IDE autocomplete support
- Runtime type validation

✅ **Easy Testing**
- Schemas can be tested independently
- Mock validated_data in tests
- Clear input/output contracts

## How to Use in Your Routes

### Step 1: Import Schema and Decorator
```python
from schemas.auth_schemas import UserRegisterSchema, UserLoginSchema
from utils.validators import validate_request
```

### Step 2: Add Decorator to Route
```python
@router.post("/register")
@validate_request(UserRegisterSchema)
async def register(request: Request, validated_data: dict):
    # Use validated_data here
```

### Step 3: Handle Validated Data
```python
async def register(request: Request, validated_data: dict):
    # validated_data['username'] - already validated username
    # validated_data['email'] - already validated and lowercased email
    # validated_data['password'] - already validated password
    user = create_user(**validated_data)
    return user
```

## Validation Error Handling

The decorator automatically returns proper HTTP error responses:

```python
# If validation fails, automatically returns:
{
    "detail": {
        "status": "validation_error",
        "errors": {
            "field_name": ["error message"]
        }
    }
}
# with status code 422 UNPROCESSABLE_ENTITY
```

## Full Integration Checklist

- [x] Create `schemas/` directory
- [x] Create `utils/` directory
- [x] Implement `auth_schemas.py` with Marshmallow schemas
- [x] Implement `storage_schemas.py` for storage validation
- [x] Create `validators.py` with `@validate_request` decorator
- [x] Update `requirements.txt` with Marshmallow packages
- [ ] Update each route function to use `@validate_request` decorator
- [ ] Remove Pydantic validators from routes (optional - can keep both)
- [ ] Update tests to work with new validation system

## Next Steps

1. **Apply to all routes:**
   - `/api/auth/login` → `@validate_request(UserLoginSchema)`
   - `/api/auth/register` → `@validate_request(UserRegisterSchema)`
   - `/api/storage/*` → Storage schemas
   - `/api/prediction/*` → Prediction schemas

2. **Update tests:**
   - Test schema validation directly
   - Test route with mocked validated_data
   - Test error responses

3. **Optional: Deprecate Pydantic models**
   - Keep for backward compatibility initially
   - Gradually migrate to Marshmallow schemas
   - Document the transition

## Running the New System

```bash
# Install new dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload

# Test the register endpoint
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'

# Should return 201 with tokens
# Or 422 with validation errors if data is invalid
```

---

This integration provides a clean, maintainable validation system using industry-standard Marshmallow schemas alongside FastAPI! 🚀
