"""
Input Validation Decorator

Provides a decorator for validating request data using Marshmallow schemas.
Automatically deserializes and validates incoming JSON data against schemas.
"""

from functools import wraps
from typing import Callable, Type, Any, Dict
from fastapi import Request, HTTPException, status
from marshmallow import Schema, ValidationError, RAISE
import json


class ValidatorDecorator:
    """
    Decorator for validating FastAPI request data with Marshmallow schemas.
    
    Handles:
    - Automatic request JSON deserialization
    - Schema validation
    - Error response formatting
    - Type hint preservation
    """
    
    @staticmethod
    def validate_request(schema_class: Type[Schema], many: bool = False):
        """
        Decorator to validate request data against a Marshmallow schema.
        
        Args:
            schema_class: Marshmallow schema class to validate against
            many: Whether to validate multiple objects
            
        Returns:
            Callable: Decorated function
            
        Example:
            from schemas.auth_schemas import UserRegisterSchema
            
            @app.post("/register")
            @validate_request(UserRegisterSchema)
            async def register(request: Request, validated_data: Dict):
                # validated_data contains deserialized and validated data
                user = create_user(validated_data)
                return {"status": "success", "user_id": user.id}
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
                try:
                    # Get request body
                    body = await request.json()
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid JSON in request body"
                    )
                
                # Initialize schema
                schema = schema_class(many=many, unknown=RAISE)
                
                # Validate and deserialize data
                try:
                    validated_data = schema.load(body)
                except ValidationError as e:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "status": "validation_error",
                            "errors": e.messages
                        }
                    )
                
                # Pass validated data to the route function
                kwargs['validated_data'] = validated_data
                return await func(request, *args, **kwargs)
            
            return wrapper
        
        return decorator


# Export the decorator for easy import
validate_request = ValidatorDecorator.validate_request


def create_error_response(schema: Schema, errors: Dict) -> Dict:
    """
    Format Marshmallow validation errors for API response.
    
    Args:
        schema: The Marshmallow schema that was validated
        errors: Validation errors dictionary from schema.load()
        
    Returns:
        dict: Formatted error response
        
    Example:
        {
            "status": "validation_error",
            "message": "Request validation failed",
            "errors": {
                "email": ["Invalid email format"],
                "password": ["Password must be at least 8 characters"]
            },
            "error_count": 2
        }
    """
    return {
        "status": "validation_error",
        "message": "Request validation failed",
        "errors": errors,
        "error_count": sum(1 for v in errors.values() if v),
    }


def validate_data(schema_class: Type[Schema], data: Dict, many: bool = False) -> tuple[bool, Any, Dict]:
    """
    Standalone function to validate data using a Marshmallow schema.
    
    Args:
        schema_class: Marshmallow schema class
        data: Data dictionary to validate
        many: Whether to validate multiple objects
        
    Returns:
        tuple: (is_valid, validated_data, errors)
        
    Example:
        is_valid, data, errors = validate_data(UserRegisterSchema, request_data)
        if not is_valid:
            print(errors)  # {"email": ["Invalid email format"]}
        else:
            create_user(data)
    """
    schema = schema_class(many=many, unknown=RAISE)
    
    try:
        validated_data = schema.load(data)
        return True, validated_data, {}
    except ValidationError as e:
        return False, None, e.messages


def serialize_data(schema_class: Type[Schema], data: Any, many: bool = False) -> Dict:
    """
    Serialize data using a Marshmallow schema (dump operation).
    
    Args:
        schema_class: Marshmallow schema class
        data: Data object(s) to serialize
        many: Whether to serialize multiple objects
        
    Returns:
        dict: Serialized data
        
    Example:
        user_dict = serialize_data(UserResponseSchema, user_object)
    """
    schema = schema_class(many=many)
    return schema.dump(data)


# ========================
# Schema Validation Helpers
# ========================

class SchemaValidator:
    """
    Helper class for working with Marshmallow schemas.
    
    Provides convenient methods for validation, serialization, and error handling.
    """
    
    @staticmethod
    def validate_and_load(schema_class: Type[Schema], data: Dict) -> tuple[bool, Any]:
        """
        Validate and load data, returning success status and data/errors.
        
        Args:
            schema_class: Marshmallow schema class
            data: Data to validate
            
        Returns:
            tuple: (success: bool, result: dict or errors)
        """
        is_valid, validated_data, errors = validate_data(schema_class, data)
        
        if is_valid:
            return True, validated_data
        else:
            return False, create_error_response(schema_class(), errors)
    
    @staticmethod
    def get_schema_fields(schema_class: Type[Schema]) -> Dict[str, str]:
        """
        Get all fields from a Marshmallow schema.
        
        Args:
            schema_class: Marshmallow schema class
            
        Returns:
            dict: Field names and types
            
        Example:
            fields = SchemaValidator.get_schema_fields(UserRegisterSchema)
            # {"username": "String", "email": "Email", "password": "String"}
        """
        schema = schema_class()
        return {
            field_name: field.__class__.__name__
            for field_name, field in schema.fields.items()
        }
    
    @staticmethod
    def get_required_fields(schema_class: Type[Schema]) -> list:
        """
        Get all required fields from a Marshmallow schema.
        
        Args:
            schema_class: Marshmallow schema class
            
        Returns:
            list: Required field names
            
        Example:
            required = SchemaValidator.get_required_fields(UserRegisterSchema)
            # ["username", "email", "password"]
        """
        schema = schema_class()
        return [
            field_name
            for field_name, field in schema.fields.items()
            if field.required
        ]
