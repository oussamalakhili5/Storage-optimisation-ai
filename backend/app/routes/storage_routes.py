"""
Storage Management Routes

Secured endpoints for storage records with JWT authentication.
Data is stored in MongoDB (collection: server_metrics).

Endpoints:
    POST /api/storage                   - Create a new storage record
    GET  /api/storage                   - List storage records (paginated, filterable)
    GET  /api/storage/metrics           - Fetch the latest metrics for all servers
    GET  /api/storage/history/{server_id} - Fetch historical data for a specific server
"""

from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from bson import ObjectId

from app.database import server_metrics
from auth.decorators import get_current_user
from schemas.storage_schemas import StorageRecordCreateSchema
from utils.validators import validate_request


router = APIRouter(prefix="/api/storage", tags=["storage"])


# =========================
# Helpers
# =========================

def _serialize_record(doc: dict) -> dict:
    """Convert a MongoDB document to a JSON-serializable dict."""
    return {
        "id": str(doc["_id"]),
        "server_id": doc.get("server_id"),
        "date": doc.get("date"),
        "total_storage": doc.get("total_storage", 0),
        "used_storage": doc.get("used_storage", 0),
        "free_storage": doc.get("free_storage", 0),
        "utilization_percent": doc.get("utilization_percent", 0.0),
        "server_status": doc.get("server_status", "Inconnu"), # Added by Spark
        "cpu_usage": doc.get("cpu_usage", 0),
        "memory_usage": doc.get("memory_usage", 0),
        "read_frequency": doc.get("read_frequency", 0),
        "write_frequency": doc.get("write_frequency", 0),
    }


# =========================
# POST /api/storage
# =========================

@router.post("/", status_code=status.HTTP_201_CREATED)
@validate_request(StorageRecordCreateSchema)
async def create_storage_record(
    request: Request,
    current_user: Dict = Depends(get_current_user),
    validated_data: Dict = None,
):
    try:
        total_storage = validated_data.get("capacity_gb")
        used_storage = validated_data.get("used_gb")
        timestamp = validated_data.get("timestamp", datetime.utcnow())

        free_storage = total_storage - used_storage
        utilization_percent = (used_storage / total_storage) * 100 if total_storage > 0 else 0.0
        
        # Simulate business rules for manual inserts
        if utilization_percent < 50:
            status_val = "Normal"
        elif utilization_percent <= 80:
            status_val = "Chargé"
        else:
            status_val = "Critique"

        document = {
            "server_id": validated_data.get("device_name"),
            "date": timestamp.strftime("%Y-%m-%d") if isinstance(timestamp, datetime) else str(timestamp),
            "total_storage": total_storage,
            "used_storage": used_storage,
            "free_storage": free_storage,
            "utilization_percent": round(utilization_percent, 2),
            "server_status": status_val,
            "cpu_usage": validated_data.get("cpu_usage", 0.0),
            "memory_usage": validated_data.get("memory_usage", 0.0),
            "read_frequency": validated_data.get("read_frequency", 0.0),
            "write_frequency": validated_data.get("write_frequency", 0.0),
            "created_at": datetime.utcnow(),
        }

        result = server_metrics.insert_one(document)
        document["_id"] = result.inserted_id

        return {
            "status": "success",
            "message": "Storage record created successfully",
            "data": _serialize_record(document),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create storage record: {str(e)}")


# =========================
# GET /api/storage
# =========================

@router.get("/", status_code=status.HTTP_200_OK)
def list_storage_records(
    current_user: Dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    server_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        query_filter: Dict[str, Any] = {}

        if server_id:
            query_filter["server_id"] = server_id

        if start_date:
            query_filter.setdefault("date", {})["$gte"] = start_date

        if end_date:
            query_filter.setdefault("date", {})["$lte"] = end_date

        total_records = server_metrics.count_documents(query_filter)
        total_pages = max(1, -(-total_records // per_page))
        skip = (page - 1) * per_page

        cursor = server_metrics.find(query_filter).sort("_id", -1).skip(skip).limit(per_page)
        records_data = [_serialize_record(doc) for doc in cursor]

        return {
            "status": "success",
            "data": records_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve storage records: {str(e)}")


# ============================================
# GET /api/storage/metrics
# ============================================

@router.get("/metrics", status_code=status.HTTP_200_OK)
def get_latest_metrics(current_user: Dict = Depends(get_current_user)):
    """
    Fetches the latest metrics for all servers.
    Groups by server_id and takes the most recent record.
    """
    try:
        pipeline = [
            {"$sort": {"date": -1}},
            {"$group": {
                "_id": "$server_id",
                "latest_record": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_record"}},
            {"$sort": {"server_id": 1}}
        ]
        
        results = list(server_metrics.aggregate(pipeline))
        data = [_serialize_record(doc) for doc in results]
        
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# GET /api/storage/history/{server_id}
# ============================================

@router.get("/history/{server_id}", status_code=status.HTTP_200_OK)
def get_storage_history(
    server_id: str, 
    current_user: Dict = Depends(get_current_user)
):
    """
    Fetches the historical data (all days) for a specific server, 
    sorted by timestamp (ascending) for Recharts.
    """
    try:
        # Sort ascending by date to show history chronologically
        cursor = server_metrics.find({"server_id": server_id}).sort("date", 1)
        results = list(cursor)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No history found for server {server_id}")
            
        data = [_serialize_record(doc) for doc in results]
        
        return {
            "status": "success",
            "server_id": server_id,
            "count": len(data),
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
