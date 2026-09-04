"""
FinGraph Policy Engine Models & Schemas.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class PolicyEffect(str, Enum):
    """Result effect of a policy rule."""
    ALLOW = "ALLOW"
    DENY = "DENY"


class PolicyCondition(BaseModel):
    """Matching condition evaluated against request attributes."""
    field: str  # e.g. "role", "team_id", "hour_of_day", "resource_tenant_id"
    operator: str  # e.g. "equals", "in", "not_equals", "not_in", "contains"
    value: Any


class Policy(BaseModel):
    """Deterministic access policy rule."""
    policy_id: str = Field(default_factory=lambda: f"pol_{uuid.uuid4().hex[:10]}")
    tenant_id: str
    name: str
    description: str = ""
    resource: str  # e.g. "*", "alert", "case", "network", "user", "policy", "configuration"
    action: str  # e.g. "*", "read", "create", "update", "delete", "assign", "close", "override"
    conditions: List[PolicyCondition] = Field(default_factory=list)
    effect: PolicyEffect = PolicyEffect.ALLOW
    priority: int = Field(default=100, ge=1, le=1000)  # Lower number = higher priority
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PolicyEvaluationRequest(BaseModel):
    """Subject and resource context for authorization evaluation."""
    user_id: str
    username: Optional[str] = None
    role: str
    tenant_id: str
    org_id: Optional[str] = None
    team_ids: List[str] = Field(default_factory=list)
    resource_type: str
    resource_id: str
    resource_tenant_id: str
    action: str
    environment: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    """Decision produced by the deterministic policy engine."""
    effect: PolicyEffect
    is_allowed: bool
    matched_policy_id: Optional[str] = None
    reason: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Request Payloads
class PolicyCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    resource: str
    action: str
    conditions: Optional[List[PolicyCondition]] = None
    effect: PolicyEffect = PolicyEffect.ALLOW
    priority: Optional[int] = 100
    enabled: Optional[bool] = True


class PolicyUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    conditions: Optional[List[PolicyCondition]] = None
    effect: Optional[PolicyEffect] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
