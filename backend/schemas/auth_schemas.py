"""
Authentication Validation Schemas

Marshmallow schemas for user registration, login, and profile management.
Handles validation of email format, password strength, and user data.
"""

import re
from marshmallow import Schema, fields, validate, ValidationError, post_load
from datetime import datetime


def validate_password_strength(password: str) -> bool:
    """
    Validate password meets security requirements.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains digit
    
    Args:
        password: Password string to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        raise ValidationError("Password must contain at least one digit")
    
    return True


def validate_email_format(email: str) -> bool:
    """
    Validate email format using RFC 5322 pattern.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If email format is invalid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")
    return True


def validate_username_format(username: str) -> bool:
    """
    Validate username format.
    
    Requirements:
    - 3-50 characters
    - Only letters, numbers, underscore, hyphen
    
    Args:
        username: Username to validate
        
    Returns:
        bool: True if valid
        
    Raises:
        ValidationError: If username format is invalid
    """
    if len(username) < 3 or len(username) > 50:
        raise ValidationError("Username must be 3-50 characters long")
    
    if not re.match("^[a-zA-Z0-9_-]+$", username):
        raise ValidationError(
            "Username can only contain letters, numbers, underscore, and hyphen"
        )
    return True


# ========================
# Authentication Schemas
# ========================

class UserRegisterSchema(Schema):
    """
    Schema for user registration request validation.
    
    Fields:
        username: str - Username (3-50 chars, alphanumeric + underscore/hyphen)
        email: str - Email address (RFC 5322 format)
        password: str - Password (8+ chars, mixed case + digits)
    """
    
    username = fields.Str(
        required=True,
        validate=validate_username_format,
        metadata={"description": "Username (3-50 characters, alphanumeric + underscore/hyphen)"}
    )
    
    email = fields.Email(
        required=True,
        validate=validate_email_format,
        metadata={"description": "Email address"}
    )
    
    password = fields.Str(
        required=True,
        validate=validate_password_strength,
        load_only=True,
        metadata={"description": "Password (8+ chars, uppercase, lowercase, digits)"}
    )
    
    @post_load
    def normalize_data(self, data, **kwargs):
        """Normalize data after loading."""
        data['email'] = data['email'].lower()
        data['username'] = data['username'].strip()
        return data


class UserLoginSchema(Schema):
    """
    Schema for user login request validation.
    
    Fields:
        email: str - Email address
        password: str - Password
    """
    
    email = fields.Email(
        required=True,
        validate=validate_email_format,
        metadata={"description": "Email address"}
    )
    
    password = fields.Str(
        required=True,
        load_only=True,
        metadata={"description": "User password"}
    )
    
    @post_load
    def normalize_email(self, data, **kwargs):
        """Normalize email to lowercase."""
        data['email'] = data['email'].lower()
        return data


class UserResponseSchema(Schema):
    """
    Schema for user profile response serialization.
    
    Fields:
        id: int - User ID
        username: str - Username
        email: str - Email address
        created_at: datetime - Account creation timestamp
    """
    
    id = fields.Int(dump_only=True, metadata={"description": "User ID"})
    username = fields.Str(dump_only=True, metadata={"description": "Username"})
    email = fields.Email(dump_only=True, metadata={"description": "Email address"})
    created_at = fields.DateTime(
        dump_only=True,
        format="iso",
        allow_none=True,
        metadata={"description": "Account creation date"}
    )


class TokenResponseSchema(Schema):
    """
    Schema for authentication token response serialization.
    
    Fields:
        access_token: str - JWT access token
        refresh_token: str - JWT refresh token
        token_type: str - Token type (Bearer)
        expires_in: int - Access token expiration (minutes)
        user: UserResponseSchema - User profile data
    """
    
    access_token = fields.Str(
        required=True,
        metadata={"description": "JWT access token"}
    )
    
    refresh_token = fields.Str(
        required=True,
        metadata={"description": "JWT refresh token"}
    )
    
    token_type = fields.Str(
        dump_default="Bearer",
        metadata={"description": "Token type"}
    )
    
    expires_in = fields.Int(
        metadata={"description": "Access token expiration time in minutes"}
    )
    
    user = fields.Nested(
        UserResponseSchema,
        metadata={"description": "User profile information"}
    )
