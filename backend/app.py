"""
Application Factory for FastAPI

This module creates and configures the FastAPI application instance
with all middleware, routes, and error handlers.

Usage:
    from app_factory import create_app
    
    app = create_app()
"""

import os
import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from config import config

# ========================
# Logging Setup
# ========================

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT
)


# ========================
# App Factory Function
# ========================

def create_app(config_override: Optional[object] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        config_override: Optional configuration object to override default
        
    Returns:
        FastAPI: Configured FastAPI application instance
        
    Example:
        app = create_app()
        # or with custom config:
        from config import ProductionConfig
        app = create_app(config_override=ProductionConfig)
    """
    
    # Use provided config or default
    active_config = config_override or config
    
    # ========================
    # Create FastAPI Instance
    # ========================
    
    app = FastAPI(
        title=active_config.API_TITLE,
        description=active_config.API_DESCRIPTION,
        version=active_config.API_VERSION,
        debug=active_config.DEBUG,
    )
    
    # Store config in app state for access in routes
    app.state.config = active_config
    
    logger.info(f"Initializing application in {active_config.ENVIRONMENT} environment")
    
    # ========================
    # CORS Middleware
    # ========================
    
    if not active_config.CORS_ORIGINS or active_config.CORS_ORIGINS == ["*"]:
        logger.warning(
            "⚠️ CORS is configured with wildcard '*'. "
            "This is only acceptable in development. "
            "Use specific origins in production!"
        )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_config.CORS_ORIGINS,
        allow_credentials=active_config.CORS_CREDENTIALS,
        allow_methods=active_config.CORS_METHODS,
        allow_headers=active_config.CORS_HEADERS,
    )
    
    logger.info(
        f"CORS configured for origins: {', '.join(active_config.CORS_ORIGINS)}"
    )
    
    # ========================
    # Error Handlers
    # ========================
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        """Handle 404 Not Found errors."""
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": "Endpoint not found",
                "path": str(request.url.path),
            },
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {str(exc)}", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "detail": str(exc) if active_config.DEBUG else "Please contact support",
            },
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with detailed information."""
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "Validation error",
                "errors": exc.errors(),
            },
        )
    
    # ========================
    # Health Check Endpoint
    # ========================
    
    @app.get(
        "/health",
        tags=["monitoring"],
        summary="Health check",
        description="Check if API is running and healthy"
    )
    async def health_check():
        """
        Health check endpoint.
        
        Returns:
            dict: Service status and environment information
        """
        return {
            "status": "healthy",
            "environment": active_config.ENVIRONMENT,
            "version": active_config.API_VERSION,
        }
    
    # ========================
    # Root Endpoint
    # ========================
    
    @app.get(
        "/",
        tags=["root"],
        summary="API root",
        description="Welcome message and API information"
    )
    async def root():
        """
        Root endpoint with API information.
        
        Returns:
            dict: Welcome message and documentation links
        """
        return {
            "message": f"Welcome to {active_config.API_TITLE}",
            "version": active_config.API_VERSION,
            "environment": active_config.ENVIRONMENT,
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",
            },
        }
    
    # ========================
    # Route Registration
    # ========================
    
    # Import and register routers
    try:
        # Auth routes
        from routes.auth_routes import router as auth_router
        app.include_router(auth_router)
        logger.info("✅ Auth routes registered")
    except ImportError as e:
        logger.warning(f"Could not import auth routes: {e}")
    
    # Register storage routes if they exist
    # from routes.storage_routes import router as storage_router
    # app.include_router(storage_router)
    
    # Register prediction routes if they exist
    # from routes.prediction_routes import router as prediction_router
    # app.include_router(prediction_router)
    
    logger.info("✅ Application initialized successfully")
    
    return app


# ========================
# Application Instance
# ========================

# Create the main app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )
