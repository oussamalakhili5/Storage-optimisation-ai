"""
Backend Setup and Configuration Guide

This document explains the authentication system setup and how to get the
backend running with proper JWT authentication.
"""

# ========================
# File Structure Overview
# ========================

BACKEND_STRUCTURE = """
backend/
├── auth/                           # JWT Authentication Module
│   ├── __init__.py
│   ├── jwt_manager.py             # Token generation, password hashing
│   ├── decorators.py              # Token verification decorators
│   └── JWT_DOCUMENTATION.md
│
├── routes/                         # Routes Module (NEW - Production Ready)
│   ├── __init__.py
│   └── auth_routes.py             # ✅ Use this one (Complete implementation)
│
├── app/
│   ├── routes/                    # Legacy Routes Module
│   │   └── auth_routes.py         # Old implementation (for reference)
│   ├── models/
│   │   ├── user.py
│   │   └── storage_record.py
│   ├── database.py
│   └── config.py
│
├── main.py                         # FastAPI application entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── CURL_TEST_COMMANDS.md          # API testing guide
├── test_auth_routes.sh            # Automated test script
└── JWT_DOCUMENTATION.md           # Complete JWT documentation
"""


# ========================
# QUICK START (5 minutes)
# ========================

QUICK_START = """
1. Setup Environment Variables
   ────────────────────────────────
   
   cd backend
   cp .env.example .env
   
   # Generate secure SECRET_KEY
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Edit .env and paste the generated key as SECRET_KEY


2. Install Dependencies
   ────────────────────────────────
   
   pip install -r requirements.txt


3. Start the Backend
   ────────────────────────────────
   
   python main.py
   
   # Or with uvicorn directly:
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload


4. Test the API
   ────────────────────────────────
   
   # In another terminal:
   bash test_auth_routes.sh
   
   # Or manually:
   curl -X GET http://localhost:8000/api/auth/health
"""


# ========================
# Environment Variables (.env)
# ========================

ENV_SETUP = """
# Create backend/.env with:

SECRET_KEY=<generated-key-from-secrets>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
DATABASE_URL=postgresql+psycopg://admin:admin123@localhost:5433/storage_db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
HDFS_URL=http://localhost:9870
HDFS_FILE_PATH=/data/storage/storage_data.csv
HDFS_USER=root
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG=True
"""


# ========================
# API Endpoints Reference
# ========================

ENDPOINTS = """
Authentication Endpoints:

1. POST /api/auth/register
   Register a new user
   
   Request:
   {
     "username": "john_doe",
     "email": "john@example.com",
     "password": "SecurePass123"
   }
   
   Response: 201 Created
   {
     "access_token": "...",
     "refresh_token": "...",
     "token_type": "bearer",
     "user": { "id": 1, "username": "...", "email": "..." }
   }
   
   
2. POST /api/auth/login
   Authenticate user
   
   Request:
   {
     "email": "john@example.com",
     "password": "SecurePass123"
   }
   
   Response: 200 OK
   {
     "access_token": "...",
     "refresh_token": "...",
     "token_type": "bearer"
   }


3. GET /api/auth/me (Protected)
   Get current user profile
   
   Headers:
   Authorization: Bearer <access_token>
   
   Response: 200 OK
   {
     "id": 1,
     "username": "john_doe",
     "email": "john@example.com",
     "created_at": "2026-06-17T..."
   }


4. POST /api/auth/logout (Protected)
   Logout user
   
   Headers:
   Authorization: Bearer <access_token>
   
   Response: 200 OK
   {
     "message": "Logout successful. Please delete your tokens from client."
   }


5. GET /api/auth/health
   Health check (no authentication required)
   
   Response: 200 OK
   {
     "message": "Authentication service is healthy"
   }
"""


# ========================
# Validation Rules
# ========================

VALIDATION = """
Password Requirements:
✓ Minimum 8 characters
✓ At least one uppercase letter (A-Z)
✓ At least one lowercase letter (a-z)
✓ At least one digit (0-9)

Examples:
✅ SecurePass123   - Valid
✅ MyPassword99    - Valid
❌ secure123       - Missing uppercase
❌ SECURE123       - Missing lowercase
❌ SecurePass      - Missing digits
❌ Pass1           - Too short (< 8)


Username Requirements:
✓ 3-50 characters
✓ Letters, numbers, underscore, hyphen only
✓ No spaces or special characters

Examples:
✅ john_doe        - Valid
✅ user-123        - Valid
✅ JohnDoe         - Valid
❌ john doe        - Contains space
❌ john@doe        - Contains @


Email Requirements:
✓ Valid RFC 5322 format
✓ Must contain @
✓ Must contain domain

Examples:
✅ john@example.com        - Valid
✅ john.doe@company.co.uk  - Valid
❌ john@example             - Missing TLD
❌ john.example.com         - Missing @
❌ @example.com             - Missing username
"""


# ========================
# Testing
# ========================

TESTING = """
Automated Testing:
──────────────────

Run the full test suite:
    bash test_auth_routes.sh

This will test:
  ✓ Health check
  ✓ User registration
  ✓ Input validation
  ✓ Login/authentication
  ✓ Protected endpoints
  ✓ Error handling


Manual Testing with curl:
──────────────────────────

See: CURL_TEST_COMMANDS.md for detailed examples

Quick test:
  
  # Health check
  curl http://localhost:8000/api/auth/health
  
  # Register
  curl -X POST http://localhost:8000/api/auth/register \\
    -H "Content-Type: application/json" \\
    -d '{
      "username": "testuser",
      "email": "test@example.com",
      "password": "TestPass123"
    }'
  
  # Save the access_token and use it:
  TOKEN="<paste_access_token_here>"
  
  # Get profile
  curl http://localhost:8000/api/auth/me \\
    -H "Authorization: Bearer $TOKEN"
"""


# ========================
# Security Notes
# ========================

SECURITY = """
Authentication & Authorization:
────────────────────────────────

1. JWT Tokens
   - Signed with HS256 algorithm
   - Access tokens: 15 minutes expiration
   - Refresh tokens: 7 days expiration
   - Stored in Authorization Bearer header

2. Password Hashing
   - bcrypt with 12 rounds
   - Automatic salt generation
   - One-way hashing (cannot be reversed)

3. CORS (Cross-Origin Resource Sharing)
   - Restricted to: http://localhost:5173
   - Methods: GET, POST, PUT, DELETE, OPTIONS
   - Headers: Content-Type, Authorization

4. Error Messages
   - Generic messages to prevent user enumeration
   - "Invalid email or password" for both cases
   - "Registration failed" without specifics
   - Prevents attackers from determining valid emails

5. Input Validation
   - Email format validation (RFC 5322)
   - Password strength requirements
   - Username format validation
   - Input sanitization against injection

6. Protected Endpoints
   - Require valid JWT token in Authorization header
   - Token signature verified on every request
   - Expired tokens rejected automatically
   - Malformed tokens rejected with 401 Unauthorized
"""


# ========================
# Docker Deployment
# ========================

DOCKER = """
Build and Run with Docker:
──────────────────────────

1. Build the image:
   docker build -t storage-api:latest -f Dockerfile .

2. Run the container:
   docker run -p 8000:8000 \\
     -e SECRET_KEY=<your-secret-key> \\
     -e DATABASE_URL=postgresql+psycopg://admin:admin123@postgres:5432/storage_db \\
     --network storage-network \\
     storage-api:latest

3. Or use Docker Compose:
   docker-compose up -d backend


Environment Variables in Docker:
────────────────────────────────

Set via:
  - docker run -e VAR=value
  - docker-compose.yml environment section
  - .env file (if using docker-compose)

Required:
  SECRET_KEY - JWT signing key (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
  DATABASE_URL - PostgreSQL connection string

Optional (defaults provided):
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=15
  REFRESH_TOKEN_EXPIRE_DAYS=7
  BCRYPT_ROUNDS=12
  CORS_ORIGINS=http://localhost:5173
"""


# ========================
# Troubleshooting
# ========================

TROUBLESHOOTING = """
Common Issues & Solutions:
─────────────────────────

1. "Secret key not configured"
   Problem: SECRET_KEY environment variable not set
   Solution: 
     - Generate key: python -c "import secrets; print(secrets.token_urlsafe(32))"
     - Add to .env: SECRET_KEY=<generated-key>
     - Or set env var: export SECRET_KEY=<key>

2. "Invalid token"
   Problem: JWT token is malformed or expired
   Solution:
     - Check token expiration (access: 15 min, refresh: 7 days)
     - Request new token via /api/auth/login or refresh endpoint
     - Ensure Bearer prefix: Authorization: Bearer <token>

3. "Database connection failed"
   Problem: PostgreSQL not running or wrong credentials
   Solution:
     - Ensure PostgreSQL is running
     - Check DATABASE_URL in .env
     - Verify credentials match docker-compose.yml
     - For Docker: use service name (postgres) not localhost

4. "Port 8000 already in use"
   Problem: Another process using the port
   Solution:
     - Kill process: lsof -i :8000 | kill -9 <PID>
     - Or use different port: uvicorn main:app --port 8001

5. "CORS error in browser"
   Problem: Frontend on different origin not allowed
   Solution:
     - Add frontend URL to CORS_ORIGINS in .env
     - CORS_ORIGINS=http://localhost:5173,http://yourdomain.com
     - Restart backend to apply changes

6. "Password validation failed"
   Problem: Password doesn't meet requirements
   Solution:
     - Use 8+ characters
     - Include: Uppercase, lowercase, digits
     - Example: SecurePass123

7. "User already exists"
   Problem: Trying to register with existing email/username
   Solution:
     - Use different email
     - Use different username
     - Login if user is already registered

8. "401 Unauthorized on protected endpoint"
   Problem: Missing or invalid token
   Solution:
     - Include Authorization header: Authorization: Bearer <token>
     - Get new token from /api/auth/login
     - Check if token is expired (15 minutes)
"""


# ========================
# Running Tests
# ========================

TESTING_COMMANDS = """
Run Test Suite:
───────────────

1. Automated tests (requires bash, curl, jq):
   
   cd backend
   bash test_auth_routes.sh

2. Manual curl commands (see CURL_TEST_COMMANDS.md):
   
   # Health check
   curl http://localhost:8000/api/auth/health
   
   # Register
   curl -X POST http://localhost:8000/api/auth/register \\
     -H "Content-Type: application/json" \\
     -d '{"username":"test","email":"test@example.com","password":"Test123"}'

3. Using Python (from backend directory):
   
   from auth.jwt_manager import hash_password, verify_password
   
   # Test password hashing
   hashed = hash_password("SecurePass123")
   assert verify_password("SecurePass123", hashed) == True
"""


# ========================
# Next Steps
# ========================

NEXT_STEPS = """
1. ✅ Setup environment (.env)
2. ✅ Install dependencies (pip install -r requirements.txt)
3. ✅ Run backend (python main.py)
4. ✅ Test endpoints (bash test_auth_routes.sh)
5. ⏳ Update frontend to use JWT tokens
6. ⏳ Implement token refresh logic
7. ⏳ Add rate limiting to login endpoint
8. ⏳ Implement token blacklist for logout
9. ⏳ Add email verification
10. ⏳ Implement 2FA/MFA
"""


if __name__ == "__main__":
    print("\n=== BACKEND SETUP GUIDE ===\n")
    print(QUICK_START)
    print("\n=== FILE STRUCTURE ===\n")
    print(BACKEND_STRUCTURE)
    print("\n=== ENVIRONMENT SETUP ===\n")
    print(ENV_SETUP)
    print("\n=== API ENDPOINTS ===\n")
    print(ENDPOINTS)
    print("\n=== VALIDATION RULES ===\n")
    print(VALIDATION)
    print("\n=== TESTING ===\n")
    print(TESTING)
    print("\n=== SECURITY ===\n")
    print(SECURITY)
    print("\n=== DOCKER ===\n")
    print(DOCKER)
    print("\n=== TROUBLESHOOTING ===\n")
    print(TROUBLESHOOTING)
    print("\n=== NEXT STEPS ===\n")
    print(NEXT_STEPS)
