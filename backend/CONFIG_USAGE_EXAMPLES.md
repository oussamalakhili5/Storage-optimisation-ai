# Configuration Usage Examples

## Quick Examples for Common Tasks

### 1. Access Configuration in Routes

```python
# In backend/routes/auth_routes.py
from fastapi import FastAPI

@app.get("/api/auth/config-info")
async def get_config_info(request: Request):
    """Get current configuration info (development only)"""
    config = request.app.state.config
    
    return {
        "environment": config.ENVIRONMENT,
        "debug": config.DEBUG,
        "api_version": config.API_VERSION,
        "cors_origins": config.CORS_ORIGINS,
    }
```

### 2. Use Configuration in Dependency Functions

```python
# In backend/auth/decorators.py
from fastapi import Depends, Request

def get_config(request: Request):
    """Dependency to get current configuration"""
    return request.app.state.config

@app.get("/protected")
async def protected_endpoint(config = Depends(get_config)):
    return {
        "message": "Access granted",
        "max_token_age": f"{config.ACCESS_TOKEN_EXPIRE_MINUTES} minutes"
    }
```

### 3. Using Config in Password Hashing

```python
# In backend/auth/jwt_manager.py
from config import config
import bcrypt

def hash_password(password: str) -> str:
    """Hash password with configurable rounds"""
    salt = bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode(), salt).decode()
```

### 4. Using Config in Token Generation

```python
# In backend/auth/jwt_manager.py
from config import config
from datetime import timedelta
import jwt

def create_access_token(data: dict) -> str:
    """Create JWT access token with configured expiration"""
    expire = datetime.utcnow() + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        config.SECRET_KEY,
        algorithm=config.JWT_ALGORITHM
    )
    return encoded_jwt
```

## Testing with Different Configurations

### Unit Tests with Testing Config

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from config import TestingConfig
from app import create_app

@pytest.fixture
def test_app():
    """Create app with testing configuration"""
    return create_app(config_override=TestingConfig())

@pytest.fixture
def test_client(test_app):
    """Create test client"""
    return TestClient(test_app)

def test_register(test_client):
    """Test user registration with testing config"""
    response = test_client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!"
    })
    assert response.status_code == 201
```

### Integration Tests with Development Config

```python
# tests/test_integration.py
import pytest
from config import DevelopmentConfig
from app import create_app

@pytest.fixture
def dev_app():
    """Create app with development configuration"""
    return create_app(config_override=DevelopmentConfig())

def test_cors_headers(dev_app):
    """Verify CORS headers are set correctly"""
    from fastapi.testclient import TestClient
    client = TestClient(dev_app)
    
    response = client.get(
        "/api/auth/health",
        headers={"Origin": "http://localhost:5173"}
    )
    assert "Access-Control-Allow-Origin" in response.headers
```

## Environment-Specific Startup

### Development Startup

```python
# Create .env with development settings
if __name__ == "__main__":
    import os
    os.environ.setdefault("ENVIRONMENT", "development")
    
    from app import create_app
    import uvicorn
    
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

### Production Startup

```python
# Create .env.production with production settings
if __name__ == "__main__":
    import os
    os.environ.setdefault("ENVIRONMENT", "production")
    
    from app import create_app
    import uvicorn
    
    app = create_app()
    # Note: Use gunicorn in production, not uvicorn
    # Command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Dynamic Configuration Reloading

```python
# backend/utils/config_loader.py
import os
from config import get_config

def reload_config():
    """Reload configuration from environment (use carefully!)"""
    # This reloads from environment variables
    return get_config()

# Usage in routes
@app.post("/admin/reload-config")
async def reload_configuration(request: Request, admin_token: str):
    """Reload configuration (admin only, development only)"""
    config = request.app.state.config
    
    if config.ENVIRONMENT != "development":
        raise HTTPException(status_code=403, detail="Admin config reload only in development")
    
    if admin_token != "dev-admin-token":
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    new_config = reload_config()
    request.app.state.config = new_config
    
    return {"message": "Configuration reloaded", "new_config": new_config.ENVIRONMENT}
```

## Logging Configuration Usage

```python
# In main.py or app.py
import logging
from config import config

# Set up logging based on configuration
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT
)

logger = logging.getLogger(__name__)

if config.DEBUG:
    logger.debug("Debug mode enabled")
else:
    logger.info(f"Running in {config.ENVIRONMENT} environment")
```

## Database Configuration Usage

```python
# In backend/app/database.py
from sqlalchemy import create_engine
from config import config

# Create engine with config
engine = create_engine(
    config.DATABASE_URL,
    echo=config.SQLALCHEMY_ECHO,
    pool_size=config.SQLALCHEMY_POOL_SIZE,
    pool_recycle=config.SQLALCHEMY_POOL_RECYCLE,
    pool_pre_ping=config.SQLALCHEMY_POOL_PRE_PING,
)

# Use configuration to control connection behavior
if config.ENVIRONMENT == "production":
    # Extra safety in production
    engine = create_engine(
        config.DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
        }
    )
```

## Conditional Features Based on Config

```python
# In backend/routes/auth_routes.py
from config import config

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Register with environment-specific features"""
    
    # Always validate
    user = validate_user(request)
    
    # Send email only in production
    if config.ENVIRONMENT == "production":
        await send_verification_email(user.email)
    
    # Log more details in development
    if config.DEBUG:
        logger.debug(f"User registered: {user.username} ({user.email})")
    
    # Use configured token expiration
    token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return token
```

## Configuration as Dependency Injection

```python
# In backend/dependencies.py
from fastapi import Depends, Request
from config import Config

async def get_current_config(request: Request) -> Config:
    """Get current configuration as dependency"""
    return request.app.state.config

# Usage in routes
from dependencies import get_current_config

@app.get("/api/debug/config")
async def debug_config(config: Config = Depends(get_current_config)):
    """Debug endpoint showing current configuration"""
    if not config.DEBUG:
        raise HTTPException(status_code=403, detail="Debug endpoints disabled")
    
    return {
        "environment": config.ENVIRONMENT,
        "debug": config.DEBUG,
        "testing": config.TESTING,
        "cors_origins": config.CORS_ORIGINS,
        "bcrypt_rounds": config.BCRYPT_ROUNDS,
        "token_expire_minutes": config.ACCESS_TOKEN_EXPIRE_MINUTES,
    }
```

## Configuration Validation at Startup

```python
# In main.py
from app import app, create_app
from config import config

@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup"""
    
    errors = []
    
    # Check critical settings
    if not config.SECRET_KEY or config.SECRET_KEY == "change-me-in-production":
        if config.ENVIRONMENT == "production":
            errors.append("SECRET_KEY must be set for production")
    
    if config.ENVIRONMENT == "production":
        if not config.CORS_ORIGINS or config.CORS_ORIGINS == ["*"]:
            errors.append("CORS_ORIGINS must be restricted in production")
        
        if config.BCRYPT_ROUNDS < 12:
            errors.append("BCRYPT_ROUNDS should be at least 12 in production")
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        raise ValueError("Invalid configuration")
    
    logger.info(f"✅ Configuration validated for {config.ENVIRONMENT} environment")
```

## Multi-Tenant Configuration

```python
# For applications serving multiple organizations

# In config.py
from typing import Dict

class MultiTenantConfig(Config):
    """Configuration supporting multiple tenants"""
    
    TENANT_DATABASE_MAP: Dict[str, str] = {
        "tenant1": "postgresql://user:pass@db1/tenant1_db",
        "tenant2": "postgresql://user:pass@db2/tenant2_db",
    }
    
    TENANT_CORS_MAP: Dict[str, list] = {
        "tenant1": ["https://tenant1.com"],
        "tenant2": ["https://tenant2.com"],
    }

# Usage in routes
@app.get("/api/tenant/{tenant_id}/status")
async def tenant_status(tenant_id: str, config: MultiTenantConfig = Depends()):
    """Get status for specific tenant"""
    if tenant_id not in config.TENANT_DATABASE_MAP:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "tenant": tenant_id,
        "database": config.TENANT_DATABASE_MAP[tenant_id],
        "allowed_origins": config.TENANT_CORS_MAP[tenant_id],
    }
```

## Configuration Hot Reload (Advanced)

```python
# backend/utils/hot_reload.py
import os
from typing import Optional
from config import get_config

class ConfigManager:
    """Manager for hot reloading configuration"""
    
    _instance: Optional['ConfigManager'] = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def config(self):
        """Get current configuration, reloading if needed"""
        return get_config()
    
    def reload(self):
        """Force reload of configuration"""
        self._config = get_config()
        return self._config

# Usage
config_manager = ConfigManager()

# Access config
current_config = config_manager.config

# Reload on demand
config_manager.reload()
```

## References

- [Full Configuration Documentation](CONFIG_DOCUMENTATION.md)
- [CORS Security Guide](CORS_SECURITY_GUIDE.md)
- [Docker Configuration](DOCKER_CONFIGURATION.md)
- [Setup Guide](SETUP_GUIDE.md)
- [Phase 1.4 Implementation](PHASE_1.4_IMPLEMENTATION.md)
