"""Authentication models."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class Role(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API = "api"  # For service accounts


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    roles: List[Role] = Field(default_factory=lambda: [Role.VIEWER])
    disabled: bool = False
    api_key: Optional[str] = None


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    roles: List[Role] = Field(default_factory=list)


class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class APIKeyRequest(BaseModel):
    """API key generation request."""
    name: str
    description: Optional[str] = None
    roles: List[Role] = Field(default_factory=lambda: [Role.API])
    expires_days: int = 365


class APIKeyResponse(BaseModel):
    """API key response."""
    api_key: str
    name: str
    created_at: str
    expires_at: str

