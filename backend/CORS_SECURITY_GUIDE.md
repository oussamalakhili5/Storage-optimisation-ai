# CORS Security Configuration Guide

## Overview

Cross-Origin Resource Sharing (CORS) is a critical security mechanism that controls which frontend applications can access your API. Misconfiguration can lead to security vulnerabilities.

## Security Levels

### ❌ INSECURE (Never use in production)

```python
CORS_ORIGINS = ["*"]  # Allows ANY domain
CORS_CREDENTIALS = True  # Allows credentials (VERY BAD!)
```

**Risks:**
- Anyone can access your API from any website
- Combined with credentials, attackers can make authenticated requests on behalf of users
- No protection against CSRF attacks

### ⚠️ DEVELOPMENT ONLY

```python
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
```

**Acceptable because:**
- Restricted to localhost (local development machines)
- No sensitive data exposed
- Not publicly accessible

### ✅ PRODUCTION SECURE

```python
CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://api.yourdomain.com",
]
CORS_CREDENTIALS = True  # Only if you use httpOnly cookies
```

**Security features:**
- Only specific, verified domains allowed
- HTTPS enforced (scheme matters!)
- Credentials only with httpOnly cookies
- Clear allow/deny list

## Configuration in Practice

### Step 1: Identify Your Frontend Domains

Create a list of ALL frontend applications that need API access:

```
Production Frontend:
- https://yourdomain.com        (main website)
- https://www.yourdomain.com    (www variant)
- https://app.yourdomain.com    (SPA application)

Staging Frontend:
- https://staging.yourdomain.com

Development:
- http://localhost:5173         (Vite default)
- http://localhost:3000         (alternative port)
```

### Step 2: Set Environment Variables

**.env (Local Development)**
```bash
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**.env.production**
```bash
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com
```

### Step 3: Verify Configuration

#### Check CORS Headers in Response

```bash
# Test request to your API
curl -i -X OPTIONS https://api.yourdomain.com/api/auth/login \
  -H "Origin: https://yourdomain.com"

# Should see:
# Access-Control-Allow-Origin: https://yourdomain.com
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Headers: Content-Type, Authorization
```

#### Browser Console Test

```javascript
// From your frontend at https://yourdomain.com
fetch('https://api.yourdomain.com/api/auth/health')
  .then(r => r.json())
  .then(data => console.log('✅ CORS working:', data))
  .catch(e => console.error('❌ CORS error:', e))
```

## Common CORS Issues

### Issue 1: "No 'Access-Control-Allow-Origin' header is present"

**Cause:** Your frontend domain isn't in `CORS_ORIGINS`

**Solution:**
```bash
# Add frontend domain to CORS_ORIGINS
CORS_ORIGINS=https://yourdomain.com,https://yourdomain2.com
```

### Issue 2: "Credentials mode is 'include', but Access-Control-Allow-Credentials is missing"

**Cause:** Frontend sends credentials but API doesn't allow it

**Solution:**
```python
# In config.py
CORS_CREDENTIALS = True
```

### Issue 3: "Request header 'X-Custom-Header' is not allowed"

**Cause:** Custom header not in `CORS_HEADERS` allow list

**Solution:**
```python
# In config.py
CORS_HEADERS = ["Content-Type", "Authorization", "X-Custom-Header"]
```

### Issue 4: "DELETE method is not allowed by CORS"

**Cause:** HTTP method not in `CORS_METHODS`

**Solution:**
```python
# In config.py
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
```

## Token Storage Security

### ❌ Insecure: localStorage

```javascript
// DON'T DO THIS
localStorage.setItem('token', accessToken);
// Vulnerable to XSS attacks!
```

### ✅ Secure: httpOnly Cookies

```python
# Backend: Set httpOnly cookie
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,  # JavaScript cannot access
    secure=True,    # HTTPS only
    samesite="strict",  # CSRF protection
    max_age=15*60  # 15 minutes
)
```

```javascript
// Frontend: Browser automatically sends with each request
fetch('https://api.yourdomain.com/api/auth/me', {
    credentials: 'include'  // Send cookies
})
```

## CORS vs CSRF

**CORS** protects backend from unauthorized cross-origin requests.
**CSRF** protects users from unauthorized state-changing actions.

### With Cookies + SameSite

```python
# Prevents CSRF attacks automatically
response.set_cookie(
    key="access_token",
    value=access_token,
    samesite="strict"  # Browser won't send to cross-origin POST
)
```

## Deployment Checklist

- [ ] CORS_ORIGINS contains ONLY production domains
- [ ] All origins use HTTPS (no http://)
- [ ] No wildcards (*) in production
- [ ] CORS_CREDENTIALS set appropriately
- [ ] CORS_METHODS contains only needed methods
- [ ] Custom headers in CORS_HEADERS if used
- [ ] Frontend uses httpOnly cookies (not localStorage)
- [ ] SameSite cookie policy set to "strict"
- [ ] HTTPS enforced on both frontend and backend
- [ ] SECRET_KEY is strong and unique

## Testing CORS Configuration

### Curl Test for Development

```bash
# Test that localhost is allowed
curl -i -X OPTIONS http://localhost:8000/api/auth/health \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST"

# Should return 200 and CORS headers
```

### Curl Test for Production

```bash
# Test that only your domain is allowed
curl -i -X OPTIONS https://api.yourdomain.com/api/auth/health \
  -H "Origin: https://yourdomain.com" \
  -H "Access-Control-Request-Method: POST"

# Test that other domains are rejected
curl -i -X OPTIONS https://api.yourdomain.com/api/auth/health \
  -H "Origin: https://attacker.com" \
  -H "Access-Control-Request-Method: POST"

# Should return 403 (no CORS headers)
```

## Frontend Configuration

### Vite + Vue/React

**src/api/client.js**
```javascript
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  credentials: 'include'  // Send cookies with requests
});

// Add auth token to requests
client.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
```

**.env.development**
```
VITE_API_URL=http://localhost:8000
```

**.env.production**
```
VITE_API_URL=https://api.yourdomain.com
```

## References

- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP: Cross-Origin Resource Sharing](https://owasp.org/www-community/attacks/xss/)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [SameSite Cookie Explained](https://web.dev/samesite-cookies-explained/)

## Support

If CORS is not working:

1. Check backend `CORS_ORIGINS` configuration
2. Verify frontend origin URL matches exactly
3. Ensure HTTPS in production (scheme matters!)
4. Check browser DevTools Network tab for CORS response headers
5. Look at application logs for CORS errors
6. Verify frontend makes preflight requests for complex requests

For debugging, enable verbose logging:

```bash
LOG_LEVEL=DEBUG
```

This will print CORS information to console for each request.
