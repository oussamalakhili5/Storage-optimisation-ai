"""
Configuration Management for Storage Optimization AI Backend

This module provides configuration classes for different environments:
- Development: Debug mode, verbose logging
- Production: Secure, optimized for performance
- Testing: Minimal configuration for unit tests
"""

import os
from typing import List
from datetime import timedelta


class Config:
    """Base configuration class with defaults."""
    
    # ========================
    # Flask/FastAPI Settings
    # ========================
    
    # API Configuration
    API_TITLE = "Storage Optimization AI API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "API pour l'optimisation dynamique des ressources de stockage avec Machine Learning"
    
    # ========================
    # Security Settings
    # ========================
    
    # JWT Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
    
    # CORS Configuration (NEVER use wildcard "*" in production)
    CORS_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    ]
    CORS_CREDENTIALS = True
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["Content-Type", "Authorization"]
    
    # ========================
    # Database Settings
    # ========================
    
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://admin:admin123@localhost:5433/storage_db"
    )
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_POOL_PRE_PING = True
    
    # ========================
    # Logging Settings
    # ========================
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ========================
    # Hadoop/HDFS Settings
    # ========================
    
    HDFS_URL = os.getenv("HDFS_URL", "http://localhost:9870")
    HDFS_FILE_PATH = os.getenv("HDFS_FILE_PATH", "/data/storage/storage_data.csv")
    HDFS_USER = os.getenv("HDFS_USER", "root")
    
    # ========================
    # Application Settings
    # ========================
    
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    # Enable debug mode
    DEBUG = True
    TESTING = False
    
    # Verbose database queries
    SQLALCHEMY_ECHO = True
    
    # Verbose logging
    LOG_LEVEL = "DEBUG"
    
    # Less strict CORS for development
    # Allow any localhost variant
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Weaker but acceptable for development
    BCRYPT_ROUNDS = 10
    
    # Shorter token expiration for testing
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    
    # Disable some security features for development
    CORS_CREDENTIALS = True


class ProductionConfig(Config):
    """Production environment configuration."""
    
    # Disable debug mode
    DEBUG = False
    TESTING = False
    
    # Don't echo queries
    SQLALCHEMY_ECHO = False
    
    # Production logging
    LOG_LEVEL = "WARNING"
    
    # Strict CORS configuration (must be set via environment variable)
    CORS_ORIGINS = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "https://yourdomain.com").split(",")
    ]
    
    # Stronger password hashing
    BCRYPT_ROUNDS = 14
    
    # Shorter access token lifetime for security
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    
    # Longer DB pool recycle
    SQLALCHEMY_POOL_RECYCLE = 7200


class TestingConfig(Config):
    """Testing environment configuration."""
    
    # Enable testing mode
    DEBUG = True
    TESTING = True
    
    # Use in-memory SQLite for testing
    DATABASE_URL = "sqlite:///:memory:"
    
    # Verbose logging for tests
    LOG_LEVEL = "DEBUG"
    
    # Fast password hashing for tests
    BCRYPT_ROUNDS = 4
    
    # Allow any origin for testing
    CORS_ORIGINS = ["*"]
    
    # Disable CORS credentials for testing
    CORS_CREDENTIALS = False


# ========================
# Configuration Selection
# ========================

def get_config():
    """
    Get configuration based on ENVIRONMENT variable.
    
    Environment variables:
        ENVIRONMENT: 'development', 'production', or 'testing'
        
    Returns:
        Config: Configuration class instance
        
    Raises:
        ValueError: If ENVIRONMENT is unknown
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "dev": DevelopmentConfig,
        "production": ProductionConfig,
        "prod": ProductionConfig,
        "testing": TestingConfig,
        "test": TestingConfig,
    }
    
    if environment not in config_map:
        raise ValueError(
            f"Unknown environment: {environment}. "
            f"Must be one of: {', '.join(config_map.keys())}"
        )
    
    return config_map[environment]()


# ========================
# Export Configuration
# ========================

# Get active configuration
config = get_config()

# Export all config classes and instance
__all__ = [
    "Config",
    "DevelopmentConfig",
    "ProductionConfig",
    "TestingConfig",
    "get_config",
    "config",
]
