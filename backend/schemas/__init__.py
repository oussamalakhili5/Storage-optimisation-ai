"""
Marshmallow Validation Schemas

This module provides Marshmallow schemas for data validation across the application.
Schemas handle deserialization, validation, and serialization of request/response data.

Available Schema Classes:
- Auth schemas: UserRegisterSchema, UserLoginSchema, UserResponseSchema, TokenResponseSchema
- Storage schemas: StorageRecordCreateSchema, StorageRecordResponseSchema
- Detection schemas: PredictionRequestSchema, AnomalyDetectionRequestSchema

Usage:
    from schemas.auth_schemas import UserRegisterSchema
    schema = UserRegisterSchema()
    errors = schema.validate(data)
    if errors:
        raise ValidationError(errors)
"""

from schemas.auth_schemas import (
    UserRegisterSchema,
    UserLoginSchema,
    UserResponseSchema,
    TokenResponseSchema,
)

from schemas.storage_schemas import (
    StorageRecordCreateSchema,
    StorageRecordResponseSchema,
    PredictionRequestSchema,
    AnomalyDetectionRequestSchema,
)

__all__ = [
    # Auth schemas
    "UserRegisterSchema",
    "UserLoginSchema",
    "UserResponseSchema",
    "TokenResponseSchema",
    # Storage schemas
    "StorageRecordCreateSchema",
    "StorageRecordResponseSchema",
    "PredictionRequestSchema",
    "AnomalyDetectionRequestSchema",
]
