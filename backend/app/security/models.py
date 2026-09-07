"""
FinGraph Security, RBAC & Audit Models.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class Role(str, Enum):
    """Hierarchical Role-Based Access Control roles."""
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    ADMIN = "ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"
    REVIEWER = "REVIEWER"
    AUDITOR = "AUDITOR"
    EXECUTIVE = "EXECUTIVE"
    READ_ONLY = "READ_ONLY"


class Permission(str, Enum):
    """Granular platform and resource permissions."""
    # Existing core permissions
    ALERT_READ = "ALERT_READ"
    ALERT_UPDATE = "ALERT_UPDATE"
    CASE_READ = "CASE_READ"
    CASE_CREATE = "CASE_CREATE"
    CASE_UPDATE = "CASE_UPDATE"
    CASE_ASSIGN = "CASE_ASSIGN"
    CASE_CLOSE = "CASE_CLOSE"
    EVIDENCE_READ = "EVIDENCE_READ"
    EVIDENCE_CREATE = "EVIDENCE_CREATE"
    DECISION_READ = "DECISION_READ"
    DECISION_CREATE = "DECISION_CREATE"
    DECISION_OVERRIDE = "DECISION_OVERRIDE"
    SIMULATION_RUN = "SIMULATION_RUN"
    DETECTOR_RECOMMEND = "DETECTOR_RECOMMEND"
    DETECTOR_APPROVE = "DETECTOR_APPROVE"
    DETECTOR_DEPLOY = "DETECTOR_DEPLOY"
    TENANT_ADMIN = "TENANT_ADMIN"
    USER_ADMIN = "USER_ADMIN"
    POLICY_ADMIN = "POLICY_ADMIN"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    
    # Extended Enterprise Permissions
    ANALYTICS_READ = "ANALYTICS_READ"
    REPORT_READ = "REPORT_READ"
    REPORT_CREATE = "REPORT_CREATE"
    REPORT_EXPORT = "REPORT_EXPORT"
    AUDIT_READ = "AUDIT_READ"
    TENANT_READ = "TENANT_READ"
    TENANT_WRITE = "TENANT_WRITE"
    USER_READ = "USER_READ"
    USER_WRITE = "USER_WRITE"
    TEAM_READ = "TEAM_READ"
    TEAM_WRITE = "TEAM_WRITE"


class User(BaseModel):
    """Internal user entity with hashed password credentials."""
    user_id: str = Field(default_factory=lambda: f"usr_{uuid.uuid4().hex[:10]}")
    username: str
    password_hash: str
    role: Role = Role.ANALYST
    is_active: bool = True
    tenant_id: str = "tnt_default"
    organization_id: Optional[str] = "org_default"
    team_ids: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserResponse(BaseModel):
    """Public user response without credentials."""
    user_id: str
    username: str
    role: Role
    is_active: bool
    tenant_id: Optional[str] = "tnt_default"
    organization_id: Optional[str] = "org_default"
    team_ids: Optional[List[str]] = Field(default_factory=list)
    permissions: Optional[List[str]] = Field(default_factory=list)
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
    tenant_id: Optional[str] = "tnt_default"
    organization_id: Optional[str] = "org_default"
    team_ids: Optional[List[str]] = None
    permissions: Optional[List[str]] = None


class UpdateUserRequest(BaseModel):
    """Payload for administrative user updates."""
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    team_ids: Optional[List[str]] = None
    permissions: Optional[List[str]] = None


class UserStatusTransitionRequest(BaseModel):
    """Payload to transition user state."""
    target_status: str  # ACTIVE, SUSPENDED, DISABLED
    reason: Optional[str] = ""


class AuditLog(BaseModel):
    """Forensic and administrative change audit record."""
    audit_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    user_id: str
    username: Optional[str] = None
    tenant_id: Optional[str] = "tnt_default"
    action: str  # e.g., "ALERT_STATUS_UPDATE", "ACCOUNT_FREEZE", "USER_CREATED", "TENANT_CREATED", "POLICY_CREATED"
    resource_type: str  # e.g., "ALERT", "ACCOUNT", "USER", "TENANT", "POLICY"
    resource_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    request_id: Optional[str] = None
