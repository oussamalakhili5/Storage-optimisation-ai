# Quick Start Guide - Configuration System

## 🚀 Get Started in 5 Minutes

### 1. Verify Files Are Created (30 seconds)

```bash
cd backend
ls -la config.py app.py .env.* requirements.txt
```

**Expected Output:**
```
config.py              ✅
app.py                 ✅
.env.example          ✅ (existing)
.env.production       ✅ (new)
.env.testing          ✅ (new)
requirements.txt      ✅ (updated)
```

### 2. Update Your Environment (1 minute)

**For Development:**
```bash
# Copy template (or use existing .env)
cp .env.example .env

# Edit .env
nano .env  # or use your editor

# Required settings:
ENVIRONMENT=development
SECRET_KEY=my-dev-secret-key
DATABASE_URL=postgresql://admin:admin123@localhost:5433/storage_db
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=DEBUG
```

**For Production:**
```bash
# Copy production template
cp .env.production .env.production.local

# Edit with real values
nano .env.production.local

# Update these:
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://prod_user:<strong-password>@prod-host:5432/storage_db
CORS_ORIGINS=https://yourdomain.com
```

### 3. Install Dependencies (2 minutes)

```bash
# Install updated requirements
pip install -r requirements.txt

# Or in Docker
docker-compose build
```

### 4. Test Configuration (1 minute)

```bash
# Test that configuration loads
python -c "from config import config; print(f'✅ Config: {config.ENVIRONMENT}')"

# Run health check
python main.py &
sleep 2
curl http://localhost:8000/health
kill %1
```

### 5. Deploy (1 minute)

```bash
# Development
ENVIRONMENT=development docker-compose up

# OR Production  
ENVIRONMENT=production docker-compose up -d
```

**Expected Output:**
```
backend      | INFO:     Started server process [1]
backend      | INFO:     Waiting for application startup.
backend      | ✅ Application initialized successfully
```

---

## 📋 What Was Added

### New Files Created

| File | Purpose | Location |
|------|---------|----------|
| `config.py` | Configuration classes | backend/ |
| `app.py` | App factory | backend/ |
| `.env.production` | Production template | backend/ |
| `.env.testing` | Testing template | backend/ |
| `CONFIG_DOCUMENTATION.md` | Full reference | backend/ |
| `CORS_SECURITY_GUIDE.md` | CORS how-to | backend/ |
| `DOCKER_CONFIGURATION.md` | Docker guide | backend/ |
| `CONFIG_USAGE_EXAMPLES.md` | Code examples | backend/ |
| `PHASE_1.4_IMPLEMENTATION.md` | Summary | backend/ |

### Updated Files

| File | Changes |
|------|---------|
| `requirements.txt` | Fixed encoding, added 3 packages |
| `main.py` | No changes needed (works as-is!) |

---

## 🔍 Check Configuration

### Verify Configuration Loads

```bash
python -c "
from config import config
print(f'Environment: {config.ENVIRONMENT}')
print(f'Debug: {config.DEBUG}')
print(f'CORS Origins: {config.CORS_ORIGINS}')
print(f'Bcrypt Rounds: {config.BCRYPT_ROUNDS}')
"
```

### Test Each Environment

```bash
# Test development config
ENVIRONMENT=development python -c "from config import config; print(config.ENVIRONMENT)"

# Test production config
ENVIRONMENT=production python -c "from config import config; print(config.ENVIRONMENT)"

# Test testing config
ENVIRONMENT=testing python -c "from config import config; print(config.ENVIRONMENT)"
```

---

## 🐳 Docker Usage

### Development with Hot Reload

```bash
# Start services
docker-compose up

# Backend available at http://localhost:8000
# Frontend available at http://localhost:5173
# Database at localhost:5433
```

### Production Deployment

```bash
# Create production environment
export ENVIRONMENT=production
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Start services
docker-compose -f docker-compose.yml up -d

# Check logs
docker-compose logs backend
```

---

## 🧪 Test API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","environment":"development","version":"1.0.0"}
```

### Registration

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

### Protected Endpoint (with token)

```bash
# First get a token from login response
TOKEN="your-token-here"

curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔐 Security Checklist

### Development Setup
- [ ] ENVIRONMENT=development in .env
- [ ] CORS_ORIGINS includes localhost
- [ ] LOG_LEVEL=DEBUG (or higher)
- [ ] Any SECRET_KEY works (change before prod)

### Production Setup
- [ ] ENVIRONMENT=production in .env.production
- [ ] SECRET_KEY is strong (32+ chars)
- [ ] CORS_ORIGINS has only HTTPS domains
- [ ] LOG_LEVEL=WARNING
- [ ] BCRYPT_ROUNDS=14
- [ ] DATABASE_URL has strong password
- [ ] .env files NOT in git
- [ ] Secrets in secrets manager

---

## 🛠️ Troubleshooting

### Problem: "Unknown environment"

**Solution:**
```bash
# Check environment variable
echo $ENVIRONMENT

# Set it
export ENVIRONMENT=development
python main.py
```

### Problem: CORS errors in browser

**Solution:**
```bash
# Check frontend URL matches CORS_ORIGINS
echo $CORS_ORIGINS

# Add missing domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Problem: Database connection failed

**Solution:**
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL

# Check if PostgreSQL is running
docker ps | grep postgres
```

### Problem: "SECRET_KEY must be set"

**Solution:**
```bash
# Generate strong key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in .env
SECRET_KEY=<generated-key>
```

---

## 📚 Documentation Map

**New to configuration?**
→ Start with [CONFIG_DOCUMENTATION.md](CONFIG_DOCUMENTATION.md)

**Need to secure CORS?**
→ Read [CORS_SECURITY_GUIDE.md](CORS_SECURITY_GUIDE.md)

**Using Docker?**
→ Check [DOCKER_CONFIGURATION.md](DOCKER_CONFIGURATION.md)

**Want code examples?**
→ See [CONFIG_USAGE_EXAMPLES.md](CONFIG_USAGE_EXAMPLES.md)

**Full implementation details?**
→ Review [PHASE_1.4_IMPLEMENTATION.md](PHASE_1.4_IMPLEMENTATION.md)

---

## 🚀 Next Steps

### Immediate (Today)
1. Copy `.env.example` to `.env`
2. Update with your values
3. Run `docker-compose up`
4. Test endpoints with curl

### Tomorrow
1. Review [CORS_SECURITY_GUIDE.md](CORS_SECURITY_GUIDE.md)
2. Configure production CORS origins
3. Setup secrets management

### Next Week
1. Add rate limiting
2. Implement token refresh flow
3. Add frontend integration
4. Deploy to staging

---

## 💡 Pro Tips

### Tip 1: Keep Secrets Safe
```bash
# Never commit secrets to git
echo ".env" >> .gitignore
echo ".env.*.local" >> .gitignore

# Use environment manager
# - Direnv (.envrc)
# - Python-dotenv (already installed)
# - Docker secrets
```

### Tip 2: Different .env Files

```bash
# Development
cp .env.example .env

# Production
cp .env.production .env.production.local

# Testing
cp .env.testing .env.testing.local

# Load with:
set -a
source .env
set +a
```

### Tip 3: Quick Environment Switch

```bash
# Create aliases for quick switching
alias dev="export ENVIRONMENT=development"
alias prod="export ENVIRONMENT=production"
alias test="export ENVIRONMENT=testing"

# Use:
dev
python main.py  # Runs in development
```

### Tip 4: Configuration Validation

```bash
# Validate before deploying
python -c "
from config import config
print('✅ Configuration valid!')
print(f'Environment: {config.ENVIRONMENT}')
print(f'CORS Origins: {config.CORS_ORIGINS}')
print(f'Database: {config.DATABASE_URL[:30]}...')
"
```

---

## 📞 Need Help?

### Common Commands

```bash
# View all environment variables
env | grep -E "ENVIRONMENT|SECRET|DATABASE|CORS"

# View configuration
python -c "from config import config; import json; print(json.dumps({k: str(v) for k, v in config.__dict__.items() if not k.startswith('_')}, indent=2))"

# Test CORS headers
curl -i -X OPTIONS http://localhost:8000/api/auth/login \
  -H "Origin: http://localhost:5173"

# View logs
docker-compose logs -f backend

# Restart services
docker-compose restart
```

### Files to Check

- **Configuration**: `config.py`
- **Environment**: `.env` or `.env.{ENVIRONMENT}`
- **App Setup**: `app.py`
- **Errors**: Docker logs or console

---

## ✅ Verification Checklist

After following this guide:

- [ ] `config.py` loaded successfully
- [ ] Environment variables set in `.env`
- [ ] Application starts without errors
- [ ] `/health` endpoint responds
- [ ] CORS headers present in response
- [ ] Database connection working
- [ ] Authentication endpoints functional
- [ ] Configuration matches your environment

---

**Ready to get started?** Run these commands:

```bash
# 1. Navigate to backend
cd backend

# 2. Install dependencies (if needed)
pip install -r requirements.txt

# 3. Copy example config
cp .env.example .env

# 4. Edit config
nano .env

# 5. Start application
docker-compose up
```

**All set!** Your application is now running with production-ready configuration management. 🎉

For more details, check the [CONFIG_DOCUMENTATION.md](CONFIG_DOCUMENTATION.md).
