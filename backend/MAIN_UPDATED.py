"""
Updated Main Entry Point using the App Factory Pattern

This is an example of how to update main.py to use the new app factory.
Replace the current main.py content with this for a cleaner architecture.
"""

from app import app
from auth.jwt_manager import init_jwt


# Initialize JWT with the app
init_jwt(app)


# The app is now configured with:
# ✅ CORS middleware (from config.py)
# ✅ Error handlers (from app_factory.py)
# ✅ Health check endpoint
# ✅ Root endpoint with API info
# ✅ Auth routes


if __name__ == "__main__":
    import uvicorn
    from config import config
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )
