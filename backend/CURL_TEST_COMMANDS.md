"""
Manual curl commands for testing authentication endpoints.

Copy and paste these commands into your terminal to test the API.
Make sure the backend is running on http://localhost:8000
"""

# ========================
# 1. REGISTER - Valid User
# ========================

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'

# Expected Response (201 Created):
# {
#   "access_token": "eyJhbGc...",
#   "refresh_token": "eyJhbGc...",
#   "token_type": "bearer",
#   "user": {
#     "id": 1,
#     "username": "john_doe",
#     "email": "john@example.com",
#     "created_at": "2026-06-17T12:34:56"
#   }
# }


# ========================
# 2. REGISTER - Invalid Password (Too Weak)
# ========================

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_doe",
    "email": "jane@example.com",
    "password": "weak"
  }'

# Expected Response (422 Unprocessable Entity):
# {
#   "detail": [
#     {
#       "loc": ["body", "password"],
#       "msg": "Password must be at least 8 characters long",
#       "type": "value_error"
#     }
#   ]
# }


# ========================
# 3. REGISTER - Missing Uppercase
# ========================

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_smith",
    "email": "alice@example.com",
    "password": "securepass123"
  }'

# Expected Response (422 Unprocessable Entity):
# {
#   "detail": [
#     {
#       "loc": ["body", "password"],
#       "msg": "Password must contain at least one uppercase letter",
#       "type": "value_error"
#     }
#   ]
# }


# ========================
# 4. REGISTER - Missing Lowercase
# ========================

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob_jones",
    "email": "bob@example.com",
    "password": "SECUREPASS123"
  }'

# Expected Response (422 Unprocessable Entity):
# {
#   "detail": [
#     {
#       "loc": ["body", "password"],
#       "msg": "Password must contain at least one lowercase letter",
#       "type": "value_error"
#     }
#   ]
# }


# ========================
# 5. REGISTER - Missing Numbers
# ========================

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "charlie_brown",
    "email": "charlie@example.com",
    "password": "SecurePassNoNumbers"
  }'

# Expected Response (422 Unprocessable Entity):
# {
#   "detail": [
#     {
#       "loc": ["body", "password"],
#       "msg": "Password must contain at least one digit",
#       "type": "value_error"
#     }
#   ]
# }


# ========================
# 6. REGISTER - Duplicate User
# ========================

# First, register a user (use command #1)
# Then try to register again with same email

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "different_username",
    "email": "john@example.com",
    "password": "AnotherPass123"
  }'

# Expected Response (409 Conflict):
# {
#   "detail": "Registration failed. Please try again."
# }


# ========================
# 7. REGISTER - Invalid Email
# ========================

curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "david_wilson",
    "email": "invalid.email",
    "password": "SecurePass123"
  }'

# Expected Response (422 Unprocessable Entity):
# {
#   "detail": [
#     {
#       "loc": ["body", "email"],
#       "msg": "Invalid email format",
#       "type": "value_error"
#     }
#   ]
# }


# ========================
# 8. LOGIN - Valid Credentials
# ========================

curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'

# Expected Response (200 OK):
# {
#   "access_token": "eyJhbGc...",
#   "refresh_token": "eyJhbGc...",
#   "token_type": "bearer"
# }

# ⚠️ SAVE THIS TOKEN! You'll need it for the next requests.
# Set it as environment variable:
# export ACCESS_TOKEN="<paste_token_here>"


# ========================
# 9. LOGIN - Invalid Credentials (Wrong Password)
# ========================

curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "WrongPassword123"
  }'

# Expected Response (401 Unauthorized):
# {
#   "detail": "Invalid email or password"
# }


# ========================
# 10. LOGIN - Invalid Credentials (Non-existent Email)
# ========================

curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nonexistent@example.com",
    "password": "SomePassword123"
  }'

# Expected Response (401 Unauthorized):
# {
#   "detail": "Invalid email or password"
# }

# ⚠️ Note: Same error message as wrong password (security: prevent enumeration)


# ========================
# 11. GET PROFILE - With Valid Token
# ========================

curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# Expected Response (200 OK):
# {
#   "id": 1,
#   "username": "john_doe",
#   "email": "john@example.com",
#   "created_at": "2026-06-17T12:34:56"
# }

# Replace "YOUR_ACCESS_TOKEN_HERE" with actual token from login response


# ========================
# 12. GET PROFILE - Without Token
# ========================

curl -X GET http://localhost:8000/api/auth/me

# Expected Response (403 Forbidden):
# {
#   "detail": "Not authenticated"
# }


# ========================
# 13. GET PROFILE - With Invalid Token
# ========================

curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer invalid.token.structure"

# Expected Response (401 Unauthorized):
# {
#   "detail": "Invalid token"
# }


# ========================
# 14. GET PROFILE - With Expired Token
# ========================

# After 15 minutes (default ACCESS_TOKEN_EXPIRE_MINUTES), token expires

curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <expired_token>"

# Expected Response (401 Unauthorized):
# {
#   "detail": "Token has expired"
# }


# ========================
# 15. LOGOUT
# ========================

curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# Expected Response (200 OK):
# {
#   "message": "Logout successful. Please delete your tokens from client."
# }


# ========================
# 16. HEALTH CHECK
# ========================

curl -X GET http://localhost:8000/api/auth/health

# Expected Response (200 OK):
# {
#   "message": "Authentication service is healthy"
# }


# ========================
# Using Environment Variables (Bash Script)
# ========================

# Save tokens as environment variables for easier testing:

# 1. Register or login and save response
RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }')

# 2. Extract token
export ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access_token')
export REFRESH_TOKEN=$(echo $RESPONSE | jq -r '.refresh_token')

# 3. Use in subsequent requests
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer $ACCESS_TOKEN"


# ========================
# Testing with pretty output (requires jq)
# ========================

# Install jq: https://stedolan.github.io/jq/download/

# Login and pretty-print response
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }' | jq .

# Get profile and pretty-print
curl -s -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .


# ========================
# Quick Test Sequence
# ========================

# Run these in order for a quick full test:

echo "1. Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "quicktest_'$(date +%s)'",
    "email": "quicktest_'$(date +%s)'@example.com",
    "password": "QuickTest123"
  }')
echo $REGISTER_RESPONSE | jq .

TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.access_token')

echo -e "\n2. Getting profile..."
curl -s -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n3. Logging out..."
curl -s -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n✅ All tests completed!"
