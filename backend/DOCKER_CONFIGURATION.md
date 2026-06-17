# Docker & Configuration Integration Guide

## Quick Start

### Development (Using docker-compose)

```bash
# Start services with development configuration
docker-compose up

# Backend will use:
# - ENVIRONMENT=development (from .env)
# - CORS_ORIGINS=http://localhost:5173
# - DEBUG=True
# - Hot reload enabled
```

### Production (Custom values)

```bash
# Create .env.production with your values
cp .env.production .env.production.local

# Edit with your configuration
nano .env.production.local

# Start with production environment
ENVIRONMENT=production docker-compose up -d
```

## Environment Variables in Docker

### Option 1: Using .env file

**docker-compose.yml**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - ENVIRONMENT=${ENVIRONMENT}
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
```

### Option 2: Using environment section

**docker-compose.yml**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      ENVIRONMENT: production
      SECRET_KEY: ${SECRET_KEY:-change-me}
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/storage_db
      CORS_ORIGINS: https://yourdomain.com,https://www.yourdomain.com
      LOG_LEVEL: WARNING
```

### Option 3: Using Secrets (Kubernetes/Swarm)

```yaml
version: '3.8'

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    secrets:
      - db_password
      - jwt_secret
    environment:
      DATABASE_URL: postgresql://admin:${DB_PASSWORD}@postgres:5432/storage_db
      SECRET_KEY: /run/secrets/jwt_secret
```

## Dockerfile Configuration

**backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Set environment defaults
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "main.py"]
```

## Environment-Specific Docker Compose

### Development Setup

**.dockercompose.dev.yml**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    command: python main.py
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      ENVIRONMENT: development
      LOG_LEVEL: DEBUG
    volumes:
      - ./backend:/app  # Hot reload
    depends_on:
      - postgres
  
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: storage_db
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Production Setup

**.dockercompose.prod.yml**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    environment:
      ENVIRONMENT: production
      LOG_LEVEL: WARNING
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
  
  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: storage_db
      POSTGRES_USER: prod_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U prod_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Running Different Configurations

### Development

```bash
# Using default .env
docker-compose up -d

# Or explicit development file
docker-compose -f docker-compose.dev.yml up
```

### Production

```bash
# Using production variables
docker-compose -f docker-compose.prod.yml up -d

# With environment override
ENVIRONMENT=production CORS_ORIGINS=https://yourdomain.com \
docker-compose up -d
```

### Testing

```bash
# Create test environment
export ENVIRONMENT=testing
export DATABASE_URL=sqlite:///:memory:
docker-compose -f docker-compose.test.yml up

# Run tests
docker-compose -f docker-compose.test.yml exec backend pytest
```

## Environment Variable Precedence

**Lower to Higher Priority:**

1. `.env.example` (defaults, not used in practice)
2. config.py class defaults
3. `.env` file
4. `.env.{ENVIRONMENT}` file (if exists)
5. docker-compose environment section
6. Explicit -e flag: `docker-compose run -e KEY=value`
7. OS environment variables

## Example: Setting Up Production Deployment

### Step 1: Create Production Secrets

```bash
# Generate strong secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Output: abcdef1234567890_production_secret_key

# Create secrets directory
mkdir -p ./secrets

# Store secrets
echo "your-strong-db-password" > ./secrets/db_password.txt
echo "your-strong-jwt-secret-key" > ./secrets/jwt_secret.txt

# Protect secrets
chmod 600 ./secrets/*.txt
```

### Step 2: Create Production Environment

**.env.production.local**
```bash
ENVIRONMENT=production
SECRET_KEY=$(cat ./secrets/jwt_secret.txt)
DATABASE_URL=postgresql://prod_user:$(cat ./secrets/db_password.txt)@postgres:5432/storage_db
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
LOG_LEVEL=WARNING
BCRYPT_ROUNDS=14
```

### Step 3: Deploy

```bash
# Pull latest code
git pull origin main

# Stop running containers
docker-compose down

# Pull latest images
docker-compose pull

# Start with production config
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f backend
```

## Debugging Configuration Issues

### Check What Config is Loaded

```bash
# Enter backend container
docker-compose exec backend bash

# Check environment
env | grep -E "ENVIRONMENT|SECRET|DATABASE|CORS"

# Test config import
python -c "from config import config; print(f'Config: {config.__class__.__name__}')"
```

### View Logs with Configuration Info

```bash
# Development - verbose logs
docker-compose logs -f backend

# Production - filtered logs
docker-compose logs backend | grep -E "ERROR|WARNING|CORS|JWT"
```

### Reset Configuration

```bash
# Remove all containers and data
docker-compose down -v

# Rebuild with fresh environment
docker-compose build --no-cache

# Start fresh
docker-compose up
```

## Database Initialization with Different Configs

### Development Auto-Migrate

```python
# In main.py or startup event
from sqlalchemy import text
from database import engine

@app.on_event("startup")
async def startup():
    # Create tables automatically
    Base.metadata.create_all(bind=engine)
```

### Production Explicit Migration

```bash
# Run migrations manually
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current
```

## Monitoring Configuration Changes

```bash
# Watch for changes in real-time
watch -n 1 'docker-compose ps'

# Check service health
docker-compose exec backend curl -s http://localhost:8000/health | jq .

# Monitor logs for configuration issues
docker-compose logs --tail 100 backend | grep -i "config\|cors\|database"
```

## Best Practices

✅ **DO:**
- Keep secrets out of version control
- Use different .env files for each environment
- Document all required environment variables
- Use docker-compose.override.yml for local customizations
- Set proper restart policies
- Include healthchecks
- Use secrets management in production

❌ **DON'T:**
- Commit .env files to git
- Use wildcard CORS in production
- Hardcode secrets in Dockerfile
- Use same SECRET_KEY across environments
- Run without resource limits
- Disable HTTPS in production

## References

- Docker Compose: https://docs.docker.com/compose/
- Environment Variables: https://docs.docker.com/compose/env-file/
- Secrets Management: https://docs.docker.com/engine/swarm/secrets/
- FastAPI in Containers: https://fastapi.tiangolo.com/deployment/concepts/
