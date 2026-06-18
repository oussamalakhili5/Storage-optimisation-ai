"""
Alert Management Routes

Endpoints for fetching critical alerts and server issues.
Data is read from MongoDB (collection: server_metrics).
"""

from typing import Dict
from fastapi import APIRouter, HTTPException, Depends, status

from app.database import server_metrics
from auth.decorators import get_current_user


router = APIRouter(prefix="/api/alerts", tags=["alerts"])


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
        "server_status": doc.get("server_status", "Inconnu"),
        "cpu_usage": doc.get("cpu_usage", 0),
        "memory_usage": doc.get("memory_usage", 0),
    }


# ============================================
# GET /api/alerts/critical
# ============================================

@router.get("/critical", status_code=status.HTTP_200_OK)
def get_critical_alerts(current_user: Dict = Depends(get_current_user)):
    """
    Fetches only the servers where server_status is "Critique".
    This endpoint retrieves the latest status for each server, 
    and filters out the ones that are not critical.
    """
    try:
        # We use an aggregation pipeline to:
        # 1. Group by server_id and take the most recent record
        # 2. Filter to keep only those where server_status == "Critique"
        pipeline = [
            {"$sort": {"date": -1}},
            {"$group": {
                "_id": "$server_id",
                "latest_record": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_record"}},
            {"$match": {"server_status": "Critique"}},
            {"$sort": {"utilization_percent": -1}}
        ]
        
        results = list(server_metrics.aggregate(pipeline))
        data = [_serialize_record(doc) for doc in results]
        
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve critical alerts: {str(e)}"
        )
