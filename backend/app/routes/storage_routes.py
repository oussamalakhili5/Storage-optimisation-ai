"""
Storage Management Routes

Secured CRUD endpoints for storage records with JWT authentication
and Marshmallow validation.

Endpoints:
    POST /api/storage    - Create a new storage record
    GET  /api/storage    - List storage records (paginated, filterable)
"""

from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from sqlalchemy.orm import Session
from marshmallow import ValidationError

from app.database import SessionLocal
from app.models.storage_record import StorageRecord
from auth.decorators import get_current_user
from schemas.storage_schemas import StorageRecordCreateSchema, StorageRecordResponseSchema
from utils.validators import validate_request


# =========================
# Router Configuration
# =========================

router = APIRouter(prefix="/api", tags=["storage"])


# =========================
# Database Dependency
# =========================

def get_db():
    """Provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# POST /api/storage (Create)
# =========================

@router.post("/storage", status_code=status.HTTP_201_CREATED)
@validate_request(StorageRecordCreateSchema)
async def create_storage_record(
    request: Request,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        db: Database session
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
        server_id = validated_data.get("device_name")
        total_storage = validated_data.get("capacity_gb")
        used_storage = validated_data.get("used_gb")
        timestamp = validated_data.get("timestamp", datetime.utcnow())

        # Auto-calculate derived fields
        free_storage = total_storage - used_storage
        utilization_percent = (used_storage / total_storage) * 100 if total_storage > 0 else 0.0

        # Build the storage record
        record = StorageRecord(
            server_id=server_id,
            date=timestamp.strftime("%Y-%m-%d") if isinstance(timestamp, datetime) else str(timestamp),
            total_storage=total_storage,
            used_storage=used_storage,
            free_storage=free_storage,
            cpu_usage=validated_data.get("cpu_usage", 0.0),
            memory_usage=validated_data.get("memory_usage", 0.0),
            read_frequency=validated_data.get("read_frequency", 0.0),
            write_frequency=validated_data.get("write_frequency", 0.0),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "status": "success",
            "message": "Storage record created successfully",
            "data": {
                "id": record.id,
                "server_id": record.server_id,
                "date": record.date,
                "total_storage": record.total_storage,
                "used_storage": record.used_storage,
                "free_storage": record.free_storage,
                "utilization_percent": round(utilization_percent, 2),
                "cpu_usage": record.cpu_usage,
                "memory_usage": record.memory_usage,
                "read_frequency": record.read_frequency,
                "write_frequency": record.write_frequency,
            },
        }

    except Exception as e:
        db.rollback()
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
    db: Session = Depends(get_db),
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
        db: Database session
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
        # Start building the query
        query = db.query(StorageRecord)

        # ---- Optional Filters ----

        if server_id:
            query = query.filter(StorageRecord.server_id == server_id)

        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD.",
                )
            query = query.filter(StorageRecord.date >= start_date)

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD.",
                )
            query = query.filter(StorageRecord.date <= end_date)

        # ---- Pagination ----

        total_records = query.count()
        total_pages = max(1, -(-total_records // per_page))  # ceil division
        offset = (page - 1) * per_page

        records = (
            query
            .order_by(StorageRecord.id.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # ---- Serialize Response ----

        records_data = []
        for record in records:
            utilization_percent = (
                (record.used_storage / record.total_storage) * 100
                if record.total_storage and record.total_storage > 0
                else 0.0
            )
            records_data.append({
                "id": record.id,
                "server_id": record.server_id,
                "date": record.date,
                "total_storage": record.total_storage,
                "used_storage": record.used_storage,
                "free_storage": record.free_storage,
                "utilization_percent": round(utilization_percent, 2),
                "cpu_usage": record.cpu_usage,
                "memory_usage": record.memory_usage,
                "read_frequency": record.read_frequency,
                "write_frequency": record.write_frequency,
            })

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
        # Re-raise HTTP exceptions (e.g. bad date format) as-is
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve storage records: {str(e)}",
        )
