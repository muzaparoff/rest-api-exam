"""
Data models for the User API.

This module defines SQLAlchemy ORM models and Pydantic schemas
for data validation and serialization.
"""
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

class User(Base):
    """
    SQLAlchemy User model for database storage.
    
    Represents a user with Israeli ID, name, phone number, and address.
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True, comment="Israeli ID (8-9 digits)")
    name = Column(String, nullable=False, comment="User's full name")
    phone_number = Column(String, nullable=False, comment="Israeli phone number (05XXXXXXXX)")
    address = Column(String, nullable=False, comment="User's address")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Record creation timestamp")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Record update timestamp")
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_users_phone', 'phone_number'),
        Index('idx_users_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<User(id='{self.id}', name='{self.name}', phone='{self.phone_number}')>"

class UserCreate(BaseModel):
    """
    Pydantic model for user creation requests.
    
    Validates input data before database storage.
    """
    id: str = Field(..., description="Israeli ID (8-9 digits with valid checksum)")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    phone_number: str = Field(..., description="Israeli phone number (must start with 05)")
    address: str = Field(..., min_length=1, max_length=200, description="User's address")
    
    @validator('id')
    def validate_israeli_id(cls, v):
        """Validate Israeli ID format and checksum"""
        from validators import validate_israeli_id
        
        if not validate_israeli_id(v):
            raise ValueError('Invalid Israeli ID: must be 8-9 digits with valid checksum')
        return v.strip()
    
    @validator('phone_number')
    def validate_phone_format(cls, v):
        """Validate Israeli phone number format"""
        from validators import validate_phone_number
        
        if not validate_phone_number(v):
            raise ValueError('Invalid phone number: must start with 05 and be exactly 10 digits')
        
        # Normalize phone number (remove formatting)
        import re
        return re.sub(r'\D', '', v)
    
    @validator('name')
    def validate_name(cls, v):
        """Validate user name"""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        # Basic name validation
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        
        return v.strip()
    
    @validator('address')
    def validate_address(cls, v):
        """Validate user address"""
        if not v or not v.strip():
            raise ValueError('Address cannot be empty')
        
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123456782",
                "name": "John Doe",
                "phone_number": "0501234567",
                "address": "123 Main St, Tel Aviv"
            }
        }

class UserUpdate(BaseModel):
    """
    Pydantic model for user update requests.
    
    All fields are optional for partial updates.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's full name")
    phone_number: Optional[str] = Field(None, description="Israeli phone number (must start with 05)")
    address: Optional[str] = Field(None, min_length=1, max_length=200, description="User's address")
    
    @validator('phone_number')
    def validate_phone_format(cls, v):
        """Validate Israeli phone number format if provided"""
        if v is not None:
            from validators import validate_phone_number
            
            if not validate_phone_number(v):
                raise ValueError('Invalid phone number: must start with 05 and be exactly 10 digits')
            
            # Normalize phone number
            import re
            return re.sub(r'\D', '', v)
        return v
    
    @validator('name')
    def validate_name(cls, v):
        """Validate user name if provided"""
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty')
            if len(v.strip()) < 2:
                raise ValueError('Name must be at least 2 characters long')
            return v.strip()
        return v
    
    @validator('address')
    def validate_address(cls, v):
        """Validate user address if provided"""
        if v is not None:
            if not v.strip():
                raise ValueError('Address cannot be empty')
            return v.strip()
        return v

class UserResponse(BaseModel):
    """
    Pydantic model for user API responses.
    
    Used for serializing user data in API responses.
    """
    id: str = Field(..., description="Israeli ID")
    name: str = Field(..., description="User's full name")
    phone_number: str = Field(..., description="Israeli phone number")
    address: str = Field(..., description="User's address")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123456782",
                "name": "John Doe",
                "phone_number": "0501234567",
                "address": "123 Main St, Tel Aviv",
                "created_at": "2023-12-01T10:00:00",
                "updated_at": "2023-12-01T10:00:00"
            }
        }

class UserList(BaseModel):
    """
    Pydantic model for paginated user list responses.
    """
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of users per page")
    
    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "123456782",
                        "name": "John Doe",
                        "phone_number": "0501234567",
                        "address": "123 Main St, Tel Aviv",
                        "created_at": "2023-12-01T10:00:00",
                        "updated_at": "2023-12-01T10:00:00"
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10
            }
        }

class HealthResponse(BaseModel):
    """
    Pydantic model for health check responses.
    """
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    database: bool = Field(..., description="Database connectivity status")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "message": "All systems operational",
                "timestamp": "2023-12-01T10:00:00",
                "database": True
            }
        }

class ErrorResponse(BaseModel):
    """
    Pydantic model for error responses.
    """
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "User not found",
                "error_code": "USER_NOT_FOUND",
                "timestamp": "2023-12-01T10:00:00"
            }
        }
