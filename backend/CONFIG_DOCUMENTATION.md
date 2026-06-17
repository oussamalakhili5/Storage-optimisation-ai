# Configuration Files Documentation

## Overview

The configuration system uses environment-based configuration classes to manage different deployment scenarios:

- **Development**: Debug mode, verbose logging, lenient CORS
- **Production**: Secure, optimized performance, strict CORS  
- **Testing**: In-memory database, fast hashing, no credentials

## Files Created

### 1. `config.py`

Central configuration file with 4 classes:

```python
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, get_config

# Get active configuration
config = get_config()  # Reads ENVIRONMENT variable

# Access configuration anywhere
config.CORS_ORIGINS
config.SECRET_KEY
config.DATABASE_URL
```

**Configuration Classes:**

| Class | Use Case | DEBUG | CORS | Hashing |
|-------|----------|-------|------|---------|
| `Config` | Base defaults | False | [env] | 12 rounds |
| `DevelopmentConfig` | Local development | True | localhost:* | 10 rounds |
| `ProductionConfig` | Live deployment | False | [env-strict] | 14 rounds |
| `TestingConfig` | Unit tests | True | * | 4 rounds |

**Environment Variables Supported:**

```bash
# Which config to use
ENVIRONMENT=development|production|testing

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12

# Database
DATABASE_URL=postgresql://user:pass@localhost:5433/storage_db

# CORS (comma-separated for production)
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com

# Logging
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# HDFS (optional)
HDFS_URL=http://localhost:9870
HDFS_FILE_PATH=/data/storage/storage_data.csv
HDFS_USER=root
```

### 2. `app.py` - App Factory Pattern

Factory function to create and configure FastAPI applications:

```python
from app import create_app, app

# Use the pre-configured app
# or create with custom config:
from config import ProductionConfig
app = create_app(config_override=ProductionConfig())
```

**Features:**

- ✅ CORS middleware with strict origin validation
- ✅ Global error handlers (404, 500, validation errors)
- ✅ Health check endpoint (`/health`)
- ✅ Root endpoint with API info (`/`)
- ✅ Automatic route registration
- ✅ Logging configuration
- ✅ Extensible middleware stack

### 3. `requirements.txt` - Updated Dependencies

Added:
- `pydantic-settings==2.1.0` - Settings management
- `python-multipart==0.0.6` - Form data support
- `email-validator==2.1.0` - Email validation

## Usage

### Option 1: Current Setup (Recommended - Minimal Changes)

Keep using `main.py` as-is. It will continue working with environment variables from `.env`:

```bash
ENVIRONMENT=development
SECRET_KEY=dev-secret-key
DATABASE_URL=postgresql://admin:admin123@localhost:5433/storage_db
CORS_ORIGINS=http://localhost:5173
```

### Option 2: Refactored Setup (Cleaner Architecture)

Replace `main.py` with contents from `MAIN_UPDATED.py`:

```python
from app import app
from auth.jwt_manager import init_jwt

init_jwt(app)

if __name__ == "__main__":
    import uvicorn
    from config import config
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=config.DEBUG)
```

## Security Features

✅ **CORS Protection**
- No wildcard origins in production
- Specific methods and headers only
- Credentials configurable per environment

✅ **BCRYPT Password Hashing**
- 12+ rounds in production
- Automatic salt generation
- Non-reversible hashing

✅ **JWT Token Management**
- HS256 algorithm
- Short-lived access tokens (15 min)
- Refresh token rotation (7 days)

✅ **Input Validation**
- Email format validation
- Password strength requirements
- Input sanitization

✅ **Error Handling**
- Generic error messages (no user enumeration)
- Detailed logging for debugging
- HTTP status codes

## Environment Setup

### Development

```bash
# .env
ENVIRONMENT=development
SECRET_KEY=my-dev-secret
DATABASE_URL=postgresql://admin:admin123@localhost:5433/storage_db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
LOG_LEVEL=DEBUG
```

### Production

```bash
# .env.production
ENVIRONMENT=production
SECRET_KEY=your-strong-production-secret-key
DATABASE_URL=postgresql://prod_user:strong_password@prod-db:5432/storage_db
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
LOG_LEVEL=WARNING
BCRYPT_ROUNDS=14
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

### Testing

```bash
# .env.testing
ENVIRONMENT=testing
DATABASE_URL=sqlite:///:memory:
CORS_ORIGINS=*
LOG_LEVEL=DEBUG
BCRYPT_ROUNDS=4
```

## Running the Application

### Option 1: With Uvicorn

```bash
# Development with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Production without reload
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
```

### Option 2: With Python

```bash
python main.py
```

### Option 3: Inside Docker

```bash
docker-compose up backend
```

## Testing Configuration

To run tests with the testing configuration:

```bash
# In test file or conftest.py
from config import TestingConfig
from app import create_app

@pytest.fixture
def test_app():
    return create_app(config_override=TestingConfig())

@pytest.fixture
def test_client(test_app):
    return TestClient(test_app)
```

## Troubleshooting

### Issue: "Unknown environment" error

**Solution:** Set `ENVIRONMENT` variable to one of: `development`, `production`, `testing`

```bash
export ENVIRONMENT=development
python main.py
```

### Issue: CORS errors in browser

**Solution:** Add your frontend URL to `CORS_ORIGINS`

```bash
CORS_ORIGINS=http://localhost:5173,https://yourfrontend.com
```

### Issue: Database connection failed

**Solution:** Verify `DATABASE_URL` format and credentials

```bash
# Test connection
psql postgresql://admin:admin123@localhost:5433/storage_db
```

### Issue: JWT token not being accepted

**Solution:** Ensure `SECRET_KEY` is consistent between token generation and verification

```bash
# Use strong random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Next Steps

1. **Copy the structure** - `config.py` and `app.py` are production-ready
2. **Update environment** - Add all required variables to `.env`
3. **Test endpoints** - Use curl commands from `CURL_TEST_COMMANDS.md`
4. **Deploy** - Use `ProductionConfig` with secure credentials

For detailed endpoint testing, see: [CURL_TEST_COMMANDS.md](CURL_TEST_COMMANDS.md)
For setup assistance, see: [SETUP_GUIDE.md](SETUP_GUIDE.md)

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Uvicorn: https://www.uvicorn.org/
- CORS Specification: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
