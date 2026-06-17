"""
Storage & Prediction Validation Schemas

Marshmallow schemas for storage records, predictions, and anomaly detection.
Handles validation of storage metrics and prediction requests.
"""

from marshmallow import Schema, fields, validate, ValidationError, post_load
from datetime import datetime


def validate_storage_capacity(value: float) -> bool:
    """
    Validate storage capacity is positive.
    
    Args:
        value: Capacity in GB
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if value <= 0:
        raise ValidationError("Capacity must be greater than 0 GB")
    return True


def validate_used_vs_capacity(data: dict) -> None:
    """
    Validate that used storage doesn't exceed capacity.
    
    Args:
        data: Dictionary with 'used_gb' and 'capacity_gb'
        
    Raises:
        ValidationError: If used > capacity
    """
    if data.get('used_gb', 0) > data.get('capacity_gb', float('inf')):
        raise ValidationError("Used storage cannot exceed total capacity")


def validate_percentage(value: float) -> bool:
    """
    Validate value is a valid percentage (0-100).
    
    Args:
        value: Percentage value
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If invalid
    """
    if not 0 <= value <= 100:
        raise ValidationError("Value must be between 0 and 100 percent")
    return True


# ========================
# Storage Schemas
# ========================

class StorageRecordCreateSchema(Schema):
    """
    Schema for creating storage records.
    
    Fields:
        device_name: str - Storage device name
        used_gb: float - Used storage in GB
        capacity_gb: float - Total capacity in GB
        utilization_percent: float - Utilization percentage (0-100)
        timestamp: datetime - Record timestamp
    """
    
    device_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={"description": "Storage device name"}
    )
    
    used_gb = fields.Float(
        required=True,
        validate=validate.Range(min=0),
        metadata={"description": "Used storage in GB"}
    )
    
    capacity_gb = fields.Float(
        required=True,
        validate=validate_storage_capacity,
        metadata={"description": "Total storage capacity in GB"}
    )
    
    utilization_percent = fields.Float(
        required=True,
        validate=validate_percentage,
        metadata={"description": "Utilization percentage (0-100)"}
    )
    
    timestamp = fields.DateTime(
        missing=datetime.utcnow,
        metadata={"description": "Record timestamp"}
    )
    
    @post_load
    def validate_storage_consistency(self, data, **kwargs):
        """Validate storage metrics consistency."""
        validate_used_vs_capacity(data)
        
        # Verify utilization matches used/capacity ratio
        if data.get('capacity_gb') > 0:
            calculated_util = (data.get('used_gb', 0) / data['capacity_gb']) * 100
            expected_util = data.get('utilization_percent', 0)
            
            # Allow 1% tolerance for rounding
            if abs(calculated_util - expected_util) > 1:
                raise ValidationError(
                    f"Utilization percentage doesn't match used/capacity ratio"
                )
        
        return data


class StorageRecordResponseSchema(Schema):
    """
    Schema for storage record response serialization.
    
    Fields:
        id: int - Record ID
        device_name: str - Device name
        used_gb: float - Used storage
        capacity_gb: float - Total capacity
        utilization_percent: float - Utilization percentage
        timestamp: datetime - Record timestamp
        created_at: datetime - Creation timestamp
    """
    
    id = fields.Int(dump_only=True, metadata={"description": "Record ID"})
    device_name = fields.Str(metadata={"description": "Storage device name"})
    used_gb = fields.Float(metadata={"description": "Used storage in GB"})
    capacity_gb = fields.Float(metadata={"description": "Total capacity in GB"})
    utilization_percent = fields.Float(
        metadata={"description": "Utilization percentage"}
    )
    timestamp = fields.DateTime(
        format="iso",
        metadata={"description": "Record timestamp"}
    )
    created_at = fields.DateTime(
        dump_only=True,
        format="iso",
        metadata={"description": "Creation timestamp"}
    )


# ========================
# Prediction Schemas
# ========================

class PredictionRequestSchema(Schema):
    """
    Schema for prediction request validation.
    
    Fields:
        device_id: int - Storage device ID
        periods: int - Number of periods to forecast (1-365)
        include_confidence: bool - Include confidence intervals
    """
    
    device_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        metadata={"description": "Storage device ID"}
    )
    
    periods = fields.Int(
        missing=7,
        validate=validate.Range(min=1, max=365),
        metadata={"description": "Number of periods to forecast (1-365 days)"}
    )
    
    include_confidence = fields.Bool(
        missing=False,
        metadata={"description": "Include confidence intervals in prediction"}
    )


class PredictionResponseSchema(Schema):
    """
    Schema for prediction response serialization.
    
    Fields:
        device_id: int - Device ID
        predictions: list - Forecasted values
        confidence_intervals: list - Confidence bounds (if requested)
        forecast_date: datetime - Forecast generation date
    """
    
    device_id = fields.Int(
        metadata={"description": "Storage device ID"}
    )
    
    predictions = fields.List(
        fields.Dict(),
        metadata={"description": "Forecasted values"}
    )
    
    confidence_intervals = fields.List(
        fields.Dict(),
        allow_none=True,
        metadata={"description": "Confidence intervals for predictions"}
    )
    
    forecast_date = fields.DateTime(
        format="iso",
        metadata={"description": "Forecast generation date"}
    )


# ========================
# Anomaly Detection Schemas
# ========================

class AnomalyDetectionRequestSchema(Schema):
    """
    Schema for anomaly detection request validation.
    
    Fields:
        device_id: int - Storage device ID
        sensitivity: float - Sensitivity threshold (0.1-1.0)
        window_size: int - Analysis window in days (1-90)
    """
    
    device_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        metadata={"description": "Storage device ID"}
    )
    
    sensitivity = fields.Float(
        missing=0.7,
        validate=validate.Range(min=0.1, max=1.0),
        metadata={"description": "Anomaly sensitivity (0.1=low, 1.0=high)"}
    )
    
    window_size = fields.Int(
        missing=7,
        validate=validate.Range(min=1, max=90),
        metadata={"description": "Analysis window in days (1-90)"}
    )


class AnomalyDetectionResponseSchema(Schema):
    """
    Schema for anomaly detection response serialization.
    
    Fields:
        device_id: int - Device ID
        anomalies_detected: list - Detected anomalies
        anomaly_count: int - Number of anomalies found
        alert_level: str - Alert severity (LOW, MEDIUM, HIGH, CRITICAL)
        detection_date: datetime - Detection timestamp
    """
    
    device_id = fields.Int(
        metadata={"description": "Storage device ID"}
    )
    
    anomalies_detected = fields.List(
        fields.Dict(),
        metadata={"description": "Detected anomalies with details"}
    )
    
    anomaly_count = fields.Int(
        metadata={"description": "Total number of anomalies"}
    )
    
    alert_level = fields.Str(
        validate=validate.OneOf(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
        metadata={"description": "Alert severity level"}
    )
    
    detection_date = fields.DateTime(
        format="iso",
        metadata={"description": "Detection timestamp"}
    )
