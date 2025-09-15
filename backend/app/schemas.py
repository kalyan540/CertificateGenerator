from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import uuid
import re
import html


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    
    @validator('username')
    def sanitize_username(cls, v):
        # Strip whitespace and escape HTML entities
        return html.escape(v.strip())


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    
    @validator('name')
    def validate_device_name(cls, v):
        # Strip whitespace and escape HTML entities for security
        v = html.escape(v.strip())
        
        # Allow alphanumeric characters, hyphens, and underscores only (no spaces)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Device name must contain only alphanumeric characters, hyphens, and underscores (no spaces allowed)')
        return v.lower()


class DeviceResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    
    @validator('name')
    def sanitize_name_output(cls, v):
        # Escape HTML entities for safe display
        return html.escape(v) if v else v
    
    class Config:
        from_attributes = True


class DeviceCreateResponse(BaseModel):
    device: DeviceResponse
    cert_text: str
    message: str


class DeviceCertResponse(BaseModel):
    cert_text: str
    device_name: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"
