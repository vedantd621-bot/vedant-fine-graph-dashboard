"""
FinGraph Security, RBAC & Audit Models.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class Role(str, Enum):
    """Hierarchical Role-Based Access Control roles."""
    ANALYST = "ANALYST"
    INVESTIGATOR = "INVESTIGATOR"
    ADMIN = "ADMIN"


class User(BaseModel):
    """Internal user entity with hashed password credentials."""
    user_id: str = Field(default_factory=lambda: f"usr_{uuid.uuid4().hex[:10]}")
    username: str
    password_hash: str
    role: Role = Role.ANALYST
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserResponse(BaseModel):
    """Public user response without credentials."""
    user_id: str
    username: str
    role: Role
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    """Credentials payload for JWT token acquisition."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Bearer token payload returned upon successful authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class CreateUserRequest(BaseModel):
    """Payload for administrative user creation."""
    username: str
    password: str
    role: Role = Role.ANALYST
    is_active: bool = True


class UpdateUserRequest(BaseModel):
    """Payload for administrative user updates."""
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class AuditLog(BaseModel):
    """Forensic and administrative change audit record."""
    audit_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    user_id: str
    username: Optional[str] = None
    action: str  # e.g., "ALERT_STATUS_UPDATE", "ACCOUNT_FREEZE", "USER_CREATED", "USER_ROLE_CHANGED"
    resource_type: str  # e.g., "ALERT", "ACCOUNT", "USER"
    resource_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    request_id: Optional[str] = None
