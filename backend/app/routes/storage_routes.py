"""
Storage Management Routes

Secured CRUD endpoints for storage records with JWT authentication
and Marshmallow validation. Data is stored in MongoDB (collection: server_metrics).

Endpoints:
    POST /api/storage           - Create a new storage record
    GET  /api/storage           - List storage records (paginated, filterable)
    GET  /api/storage/critical  - List servers with utilization >= 90%
"""

from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from marshmallow import ValidationError
from bson import ObjectId

from app.database import get_db, server_metrics
from auth.decorators import get_current_user
from schemas.storage_schemas import StorageRecordCreateSchema, StorageRecordResponseSchema
from utils.validators import validate_request


# =========================
# Router Configuration
# =========================

router = APIRouter(prefix="/api", tags=["storage"])


# =========================
# Helpers
# =========================

def _serialize_record(doc: dict) -> dict:
    """
    Convert a MongoDB document to a JSON-serializable dict.

    Converts ObjectId to string and computes utilization_percent on the fly.
    """
    total = doc.get("total_storage", 0)
    used = doc.get("used_storage", 0)
    utilization = (used / total) * 100 if total and total > 0 else 0.0

    return {
        "id": str(doc["_id"]),
        "server_id": doc.get("server_id"),
        "date": doc.get("date"),
        "total_storage": total,
        "used_storage": used,
        "free_storage": doc.get("free_storage", 0),
        "utilization_percent": round(utilization, 2),
        "cpu_usage": doc.get("cpu_usage", 0),
        "memory_usage": doc.get("memory_usage", 0),
        "read_frequency": doc.get("read_frequency", 0),
        "write_frequency": doc.get("write_frequency", 0),
    }


# =========================
# POST /api/storage (Create)
# =========================

@router.post("/storage", status_code=status.HTTP_201_CREATED)
@validate_request(StorageRecordCreateSchema)
async def create_storage_record(
    request: Request,
    current_user: Dict = Depends(get_current_user),
    validated_data: Dict = None,
):
    """
    Create a new storage record with automatic utilization calculation.

    Requires JWT authentication. Request body is validated against
    StorageRecordCreateSchema via Marshmallow.

    The `utilization_percent` is automatically computed as:
        (used_storage / total_storage) * 100

    Args:
        request: FastAPI Request object (used by validate_request decorator)
        current_user: Authenticated user payload from JWT token
        validated_data: Deserialized and validated request body (injected by decorator)

    Returns:
        dict: Created storage record with computed utilization_percent

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 422 if validation fails
        HTTPException: 500 if database error occurs
    """
    try:
        # Extract validated fields
        total_storage = validated_data.get("capacity_gb")
        used_storage = validated_data.get("used_gb")
        timestamp = validated_data.get("timestamp", datetime.utcnow())

        # Auto-calculate derived fields
        free_storage = total_storage - used_storage
        utilization_percent = (used_storage / total_storage) * 100 if total_storage > 0 else 0.0

        # Build the MongoDB document
        document = {
            "server_id": validated_data.get("device_name"),
            "date": timestamp.strftime("%Y-%m-%d") if isinstance(timestamp, datetime) else str(timestamp),
            "total_storage": total_storage,
            "used_storage": used_storage,
            "free_storage": free_storage,
            "utilization_percent": round(utilization_percent, 2),
            "cpu_usage": validated_data.get("cpu_usage", 0.0),
            "memory_usage": validated_data.get("memory_usage", 0.0),
            "read_frequency": validated_data.get("read_frequency", 0.0),
            "write_frequency": validated_data.get("write_frequency", 0.0),
            "created_at": datetime.utcnow(),
        }

        # Insert into MongoDB
        result = server_metrics.insert_one(document)
        document["_id"] = result.inserted_id

        return {
            "status": "success",
            "message": "Storage record created successfully",
            "data": _serialize_record(document),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create storage record: {str(e)}",
        )


# =========================
# GET /api/storage (List)
# =========================

@router.get("/storage", status_code=status.HTTP_200_OK)
def list_storage_records(
    current_user: Dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Records per page (max 100)"),
    server_id: Optional[str] = Query(None, description="Filter by server ID"),
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
):
    """
    List storage records with pagination and optional filters.

    Requires JWT authentication. Supports filtering by server_id and
    date range (start_date / end_date in YYYY-MM-DD format).

    Args:
        current_user: Authenticated user payload from JWT token
        page: Page number (default 1)
        per_page: Number of records per page (default 20, max 100)
        server_id: Optional filter by server identifier
        start_date: Optional inclusive lower bound for record date
        end_date: Optional inclusive upper bound for record date

    Returns:
        dict: Paginated list of storage records with metadata

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 400 if date format is invalid
        HTTPException: 500 if database error occurs
    """
    try:
        # ---- Build MongoDB filter ----
        query_filter: Dict[str, Any] = {}

        if server_id:
            query_filter["server_id"] = server_id

        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD.",
                )
            query_filter.setdefault("date", {})["$gte"] = start_date

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD.",
                )
            query_filter.setdefault("date", {})["$lte"] = end_date

        # ---- Pagination ----
        total_records = server_metrics.count_documents(query_filter)
        total_pages = max(1, -(-total_records // per_page))  # ceil division
        skip = (page - 1) * per_page

        cursor = (
            server_metrics
            .find(query_filter)
            .sort("_id", -1)
            .skip(skip)
            .limit(per_page)
        )

        records_data = [_serialize_record(doc) for doc in cursor]

        return {
            "status": "success",
            "data": records_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve storage records: {str(e)}",
        )


# ============================================
# GET /api/storage/critical  (Utilization ≥ 90%)
# ============================================

@router.get("/storage/critical", status_code=status.HTTP_200_OK)
def get_critical_storage(
    current_user: Dict = Depends(get_current_user),
):
    """
    Retrieve all servers whose storage utilization is at or above 90%.

    This endpoint uses a PyMongo query with the `$expr` operator to
    compute utilization on the fly:
        utilization = (used_storage / total_storage) * 100 >= 90

    Requires JWT authentication.

    Args:
        current_user: Authenticated user payload from JWT token

    Returns:
        dict: List of critical storage records sorted by utilization descending

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 500 if database error occurs
    """
    try:
        # MongoDB aggregation: compute utilization and filter >= 90%
        pipeline = [
            {
                "$addFields": {
                    "utilization_percent": {
                        "$cond": {
                            "if": {"$gt": ["$total_storage", 0]},
                            "then": {
                                "$multiply": [
                                    {"$divide": ["$used_storage", "$total_storage"]},
                                    100,
                                ]
                            },
                            "else": 0,
                        }
                    }
                }
            },
            {
                "$match": {
                    "utilization_percent": {"$gte": 90}
                }
            },
            {
                "$sort": {"utilization_percent": -1}
            },
        ]

        results = list(server_metrics.aggregate(pipeline))

        # Serialize ObjectId to string
        critical_records = []
        for doc in results:
            critical_records.append({
                "id": str(doc["_id"]),
                "server_id": doc.get("server_id"),
                "date": doc.get("date"),
                "total_storage": doc.get("total_storage"),
                "used_storage": doc.get("used_storage"),
                "free_storage": doc.get("free_storage"),
                "utilization_percent": round(doc.get("utilization_percent", 0), 2),
                "cpu_usage": doc.get("cpu_usage", 0),
                "memory_usage": doc.get("memory_usage", 0),
            })

        return {
            "status": "success",
            "count": len(critical_records),
            "data": critical_records,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve critical storage records: {str(e)}",
        )
