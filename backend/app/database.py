"""
MongoDB Database Connection Module

Provides a centralized PyMongo client and references to the database
and collections used throughout the application.

Connection string: mongodb://admin:admin123@mongodb:27017/
Database: storage_db
Collections: server_metrics, users
"""

import os
from pymongo import MongoClient


# =========================
# MongoDB Connection
# =========================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://admin:admin123@mongodb:27017/",
)

MONGO_DB_NAME = os.getenv("MONGO_DB", "storage_db")

# Create the MongoClient (connection pooling is handled automatically)
client = MongoClient(MONGO_URI)

# Reference to the database
db = client[MONGO_DB_NAME]

# =========================
# Collection References
# =========================

# Main collection for storage / server metrics
server_metrics = db["server_metrics"]

# Users collection for authentication
users = db["users"]


def get_db():
    """
    FastAPI dependency that yields the MongoDB database reference.

    Usage:
        @router.get("/example")
        def example(database = Depends(get_db)):
            collection = database["server_metrics"]
            ...
    """
    return db


def init_indexes():
    """
    Create MongoDB indexes for optimal query performance.
    Call this once at application startup.
    """
    # server_metrics indexes
    server_metrics.create_index("server_id")
    server_metrics.create_index("date")
    server_metrics.create_index([("server_id", 1), ("date", -1)])

    # users indexes (unique constraints)
    users.create_index("email", unique=True)
    users.create_index("username", unique=True)
