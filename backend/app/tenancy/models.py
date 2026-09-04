"""
FinGraph Multi-Tenant Domain Models & Quota Schemas.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    """Lifecycle status of a tenant domain."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"


class ConfigVersionStatus(str, Enum):
    """Status of an immutable configuration version."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class TenantQuota(BaseModel):
    """Resource limits and rate boundaries enforced per tenant."""
    max_users: int = Field(default=50, ge=1)
    max_teams: int = Field(default=10, ge=1)
    max_cases_per_month: int = Field(default=1000, ge=1)
    max_simulations_per_day: int = Field(default=100, ge=1)
    max_api_rps: int = Field(default=120, ge=1)


class TenantConfiguration(BaseModel):
    """Configurable operational settings for a tenant."""
    alert_priority_threshold: float = Field(default=75.0, ge=0.0, le=100.0)
    default_sla_hours: float = Field(default=4.0, ge=0.5, le=72.0)
    auto_assign_leads: bool = True
    notification_channels: List[str] = Field(default_factory=lambda: ["in_app", "websocket"])
    retention_days_audit: int = Field(default=365, ge=30)
    retention_days_cases: int = Field(default=730, ge=90)
    custom_risk_weights: Dict[str, float] = Field(default_factory=dict)


class ConfigurationVersion(BaseModel):
    """Immutable, auditable configuration release version."""
    version_id: str = Field(default_factory=lambda: f"cfg_{uuid.uuid4().hex[:10]}")
    tenant_id: str
    config_type: str = "DEFAULT"
    version: int = 1
    configuration: TenantConfiguration
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ConfigVersionStatus = ConfigVersionStatus.ACTIVE
    release_notes: Optional[str] = None


class Tenant(BaseModel):
    """Top-level enterprise tenant entity."""
    tenant_id: str = Field(default_factory=lambda: f"tnt_{uuid.uuid4().hex[:8]}")
    name: str
    slug: str
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    quotas: TenantQuota = Field(default_factory=TenantQuota)
    active_config_version: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Organization(BaseModel):
    """Business organization within a tenant domain."""
    org_id: str = Field(default_factory=lambda: f"org_{uuid.uuid4().hex[:8]}")
    tenant_id: str
    name: str
    description: str = ""
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BusinessUnit(BaseModel):
    """Operational business unit under an organization."""
    unit_id: str = Field(default_factory=lambda: f"unit_{uuid.uuid4().hex[:8]}")
    tenant_id: str
    org_id: str
    name: str
    code: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TeamMember(BaseModel):
    """User membership within an investigation team."""
    user_id: str
    username: str
    role: str
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InvestigationTeam(BaseModel):
    """Team of investigators with shared queue and case permissions."""
    team_id: str = Field(default_factory=lambda: f"team_{uuid.uuid4().hex[:8]}")
    tenant_id: str
    org_id: str
    name: str
    description: str = ""
    lead_user_id: Optional[str] = None
    members: List[TeamMember] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TenantUsageMetrics(BaseModel):
    """Aggregated resource usage for a tenant."""
    tenant_id: str
    active_users: int = 0
    active_teams: int = 0
    cases_created_this_month: int = 0
    simulations_run_today: int = 0
    transactions_processed_total: int = 0
    alerts_generated_total: int = 0
    api_requests_total: int = 0
    storage_bytes_estimate: int = 0


# Request Payloads
class TenantCreateRequest(BaseModel):
    name: str
    slug: str
    quotas: Optional[TenantQuota] = None
    initial_config: Optional[TenantConfiguration] = None


class TenantUpdateRequest(BaseModel):
    name: Optional[str] = None
    quotas: Optional[TenantQuota] = None
    metadata: Optional[Dict[str, Any]] = None


class TenantStatusTransitionRequest(BaseModel):
    target_status: TenantStatus
    reason: str


class OrganizationCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""


class BusinessUnitCreateRequest(BaseModel):
    org_id: str
    name: str
    code: str


class TeamCreateRequest(BaseModel):
    org_id: str
    name: str
    description: Optional[str] = ""
    lead_user_id: Optional[str] = None


class TeamMemberAddRequest(BaseModel):
    user_id: str
    username: str
    role: str = "INVESTIGATOR"


class ConfigVersionCreateRequest(BaseModel):
    configuration: TenantConfiguration
    release_notes: Optional[str] = None
