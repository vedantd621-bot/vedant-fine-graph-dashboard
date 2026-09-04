"""
FinGraph Tenancy & Governance Service.
Provides lifecycle management, organization hierarchies, quota enforcement, and configuration versioning.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Tuple
import uuid

from backend.app.security.audit import AuditService, get_audit_service
from backend.app.tenancy.exceptions import (
    CrossTenantAccessError,
    InvalidTenantStateTransitionError,
    OrganizationNotFoundError,
    QuotaExceededError,
    TeamNotFoundError,
    TenantNotFoundError,
    TenantSuspendedError,
)
from backend.app.tenancy.models import (
    BusinessUnit,
    BusinessUnitCreateRequest,
    ConfigVersionCreateRequest,
    ConfigVersionStatus,
    ConfigurationVersion,
    InvestigationTeam,
    Organization,
    OrganizationCreateRequest,
    TeamCreateRequest,
    TeamMember,
    TeamMemberAddRequest,
    Tenant,
    TenantConfiguration,
    TenantCreateRequest,
    TenantQuota,
    TenantStatus,
    TenantStatusTransitionRequest,
    TenantUpdateRequest,
    TenantUsageMetrics,
)


class TenancyService:
    """Central service managing multi-tenant lifecycle and organization trees."""

    LEGAL_TRANSITIONS = {
        TenantStatus.PENDING: [TenantStatus.ACTIVE, TenantStatus.DISABLED],
        TenantStatus.ACTIVE: [TenantStatus.SUSPENDED, TenantStatus.DISABLED],
        TenantStatus.SUSPENDED: [TenantStatus.ACTIVE, TenantStatus.DISABLED],
        TenantStatus.DISABLED: [TenantStatus.PENDING, TenantStatus.ACTIVE],
    }

    def __init__(self, audit_service: Optional[AuditService] = None):
        self._audit_service = audit_service or get_audit_service()
        self._tenants: Dict[str, Tenant] = {}
        self._orgs: Dict[str, Organization] = {}
        self._units: Dict[str, BusinessUnit] = {}
        self._teams: Dict[str, InvestigationTeam] = {}
        self._configs: Dict[str, List[ConfigurationVersion]] = {}
        self._usage: Dict[str, TenantUsageMetrics] = {}
        self._seed_default_tenant()

    def _seed_default_tenant(self) -> None:
        """Initializes default development tenant and organization for backward compatibility."""
        default_tenant = Tenant(
            tenant_id="tnt_default",
            name="FinGraph Core Operations",
            slug="fingraph-core",
            status=TenantStatus.ACTIVE,
            quotas=TenantQuota(max_users=100, max_teams=20, max_cases_per_month=5000, max_simulations_per_day=500, max_api_rps=300),
            metadata={"environment": "production", "tier": "ENTERPRISE"},
        )
        self._tenants[default_tenant.tenant_id] = default_tenant

        default_org = Organization(
            org_id="org_default",
            tenant_id="tnt_default",
            name="Global Fraud Risk Management",
            description="Primary risk operations organization",
        )
        self._orgs[default_org.org_id] = default_org

        default_unit = BusinessUnit(
            unit_id="unit_default",
            tenant_id="tnt_default",
            org_id="org_default",
            name="Financial Crimes Unit",
            code="FCU-01",
        )
        self._units[default_unit.unit_id] = default_unit

        default_team = InvestigationTeam(
            team_id="team_default",
            tenant_id="tnt_default",
            org_id="org_default",
            name="Syndicate Strike Team",
            description="High-priority organized fraud response squad",
            lead_user_id="usr_inv_002",
            members=[
                TeamMember(user_id="usr_inv_002", username="investigator", role="LEAD_INVESTIGATOR"),
                TeamMember(user_id="usr_ana_003", username="analyst", role="ANALYST"),
            ],
        )
        self._teams[default_team.team_id] = default_team

        initial_config = TenantConfiguration()
        v1 = ConfigurationVersion(
            version_id="cfg_default_v1",
            tenant_id="tnt_default",
            version=1,
            configuration=initial_config,
            created_by="system",
            status=ConfigVersionStatus.ACTIVE,
            release_notes="Default baseline configuration",
        )
        self._configs["tnt_default"] = [v1]
        default_tenant.active_config_version = v1.version_id

        self._usage["tnt_default"] = TenantUsageMetrics(
            tenant_id="tnt_default",
            active_users=3,
            active_teams=1,
            cases_created_this_month=14,
            simulations_run_today=25,
            transactions_processed_total=18450,
            alerts_generated_total=42,
            api_requests_total=1250,
            storage_bytes_estimate=52428800,
        )

    # -------------------------------------------------------------------------
    # Tenant Lifecycle
    # -------------------------------------------------------------------------

    def create_tenant(self, request: TenantCreateRequest, actor_id: str) -> Tenant:
        # Verify slug uniqueness
        if any(t.slug == request.slug for t in self._tenants.values()):
            raise ValueError(f"Tenant slug '{request.slug}' already exists.")

        tenant = Tenant(
            name=request.name,
            slug=request.slug,
            status=TenantStatus.ACTIVE,
            quotas=request.quotas or TenantQuota(),
        )
        self._tenants[tenant.tenant_id] = tenant

        # Initialize config
        config = request.initial_config or TenantConfiguration()
        v1 = ConfigurationVersion(
            tenant_id=tenant.tenant_id,
            version=1,
            configuration=config,
            created_by=actor_id,
            status=ConfigVersionStatus.ACTIVE,
            release_notes="Initial provisioning",
        )
        self._configs[tenant.tenant_id] = [v1]
        tenant.active_config_version = v1.version_id

        # Initialize usage
        self._usage[tenant.tenant_id] = TenantUsageMetrics(tenant_id=tenant.tenant_id)

        self._audit_service.record(
            user_id=actor_id,
            action="TENANT_CREATED",
            resource_type="TENANT",
            resource_id=tenant.tenant_id,
            new_value=json.dumps({"name": tenant.name, "slug": tenant.slug}),
        )
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant:
        if tenant_id not in self._tenants:
            raise TenantNotFoundError(f"Tenant '{tenant_id}' was not found.")
        return self._tenants[tenant_id]

    def list_tenants(self) -> List[Tenant]:
        return list(self._tenants.values())

    def update_tenant(self, tenant_id: str, request: TenantUpdateRequest, actor_id: str) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        old_val = json.dumps({"name": tenant.name, "quotas": tenant.quotas.model_dump()})

        if request.name is not None:
            tenant.name = request.name
        if request.quotas is not None:
            tenant.quotas = request.quotas
        if request.metadata is not None:
            tenant.metadata.update(request.metadata)
        tenant.updated_at = datetime.now(timezone.utc)

        self._audit_service.record(
            user_id=actor_id,
            action="TENANT_UPDATED",
            resource_type="TENANT",
            resource_id=tenant_id,
            old_value=old_val,
            new_value=json.dumps({"name": tenant.name, "quotas": tenant.quotas.model_dump()}),
        )
        return tenant

    def transition_tenant_status(
        self, tenant_id: str, request: TenantStatusTransitionRequest, actor_id: str
    ) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        current = tenant.status
        target = request.target_status

        allowed = self.LEGAL_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise InvalidTenantStateTransitionError(
                f"Cannot transition tenant from '{current.value}' to '{target.value}'. Allowed: {[s.value for s in allowed]}"
            )

        tenant.status = target
        tenant.updated_at = datetime.now(timezone.utc)

        self._audit_service.record(
            user_id=actor_id,
            action="TENANT_STATUS_CHANGED",
            resource_type="TENANT",
            resource_id=tenant_id,
            old_value=current.value,
            new_value=target.value,
        )
        return tenant

    # -------------------------------------------------------------------------
    # Organization & Team Hierarchies
    # -------------------------------------------------------------------------

    def create_organization(self, tenant_id: str, request: OrganizationCreateRequest, actor_id: str) -> Organization:
        self.get_tenant(tenant_id)
        org = Organization(
            tenant_id=tenant_id,
            name=request.name,
            description=request.description or "",
        )
        self._orgs[org.org_id] = org
        self._audit_service.record(
            user_id=actor_id,
            action="ORGANIZATION_CREATED",
            resource_type="ORGANIZATION",
            resource_id=org.org_id,
            new_value=json.dumps({"name": org.name, "tenant_id": tenant_id}),
        )
        return org

    def list_organizations(self, tenant_id: str) -> List[Organization]:
        return [o for o in self._orgs.values() if o.tenant_id == tenant_id]

    def create_business_unit(self, tenant_id: str, request: BusinessUnitCreateRequest, actor_id: str) -> BusinessUnit:
        if request.org_id not in self._orgs:
            raise OrganizationNotFoundError(f"Organization '{request.org_id}' not found.")
        unit = BusinessUnit(
            tenant_id=tenant_id,
            org_id=request.org_id,
            name=request.name,
            code=request.code,
        )
        self._units[unit.unit_id] = unit
        return unit

    def list_business_units(self, tenant_id: str, org_id: Optional[str] = None) -> List[BusinessUnit]:
        return [
            u for u in self._units.values()
            if u.tenant_id == tenant_id and (org_id is None or u.org_id == org_id)
        ]

    def create_team(self, tenant_id: str, request: TeamCreateRequest, actor_id: str) -> InvestigationTeam:
        tenant = self.get_tenant(tenant_id)
        current_teams = [t for t in self._teams.values() if t.tenant_id == tenant_id]
        if len(current_teams) >= tenant.quotas.max_teams:
            raise QuotaExceededError(f"Tenant team quota reached ({tenant.quotas.max_teams} teams max).")

        team = InvestigationTeam(
            tenant_id=tenant_id,
            org_id=request.org_id,
            name=request.name,
            description=request.description or "",
            lead_user_id=request.lead_user_id,
        )
        self._teams[team.team_id] = team

        # Update usage
        if tenant_id in self._usage:
            self._usage[tenant_id].active_teams = len(current_teams) + 1

        self._audit_service.record(
            user_id=actor_id,
            action="TEAM_CREATED",
            resource_type="TEAM",
            resource_id=team.team_id,
            new_value=json.dumps({"name": team.name, "tenant_id": tenant_id}),
        )
        return team

    def get_team(self, tenant_id: str, team_id: str) -> InvestigationTeam:
        if team_id not in self._teams:
            raise TeamNotFoundError(f"Team '{team_id}' not found.")
        team = self._teams[team_id]
        if team.tenant_id != tenant_id:
            raise CrossTenantAccessError("Team belongs to another tenant domain.")
        return team

    def list_teams(self, tenant_id: str) -> List[InvestigationTeam]:
        return [t for t in self._teams.values() if t.tenant_id == tenant_id]

    def add_team_member(self, tenant_id: str, team_id: str, request: TeamMemberAddRequest, actor_id: str) -> InvestigationTeam:
        team = self.get_team(tenant_id, team_id)
        if any(m.user_id == request.user_id for m in team.members):
            return team

        member = TeamMember(user_id=request.user_id, username=request.username, role=request.role)
        team.members.append(member)

        self._audit_service.record(
            user_id=actor_id,
            action="TEAM_MEMBER_ADDED",
            resource_type="TEAM",
            resource_id=team_id,
            new_value=json.dumps({"user_id": request.user_id, "role": request.role}),
        )
        return team

    def remove_team_member(self, tenant_id: str, team_id: str, user_id: str, actor_id: str) -> InvestigationTeam:
        team = self.get_team(tenant_id, team_id)
        team.members = [m for m in team.members if m.user_id != user_id]

        self._audit_service.record(
            user_id=actor_id,
            action="TEAM_MEMBER_REMOVED",
            resource_type="TEAM",
            resource_id=team_id,
            old_value=user_id,
        )
        return team

    # -------------------------------------------------------------------------
    # Configuration Versioning
    # -------------------------------------------------------------------------

    def create_config_version(
        self, tenant_id: str, request: ConfigVersionCreateRequest, actor_id: str
    ) -> ConfigurationVersion:
        self.get_tenant(tenant_id)
        history = self._configs.setdefault(tenant_id, [])
        next_ver = len(history) + 1

        cfg_ver = ConfigurationVersion(
            tenant_id=tenant_id,
            version=next_ver,
            configuration=request.configuration,
            created_by=actor_id,
            status=ConfigVersionStatus.DRAFT,
            release_notes=request.release_notes,
        )
        history.append(cfg_ver)
        return cfg_ver

    def activate_config_version(self, tenant_id: str, version_id: str, actor_id: str) -> ConfigurationVersion:
        tenant = self.get_tenant(tenant_id)
        history = self._configs.get(tenant_id, [])
        target = next((c for c in history if c.version_id == version_id), None)
        if not target:
            raise ValueError(f"Configuration version '{version_id}' not found.")

        # Retire previously active version
        for c in history:
            if c.status == ConfigVersionStatus.ACTIVE:
                c.status = ConfigVersionStatus.RETIRED

        target.status = ConfigVersionStatus.ACTIVE
        tenant.active_config_version = target.version_id
        tenant.updated_at = datetime.now(timezone.utc)

        self._audit_service.record(
            user_id=actor_id,
            action="CONFIGURATION_ACTIVATED",
            resource_type="CONFIGURATION",
            resource_id=version_id,
            new_value=json.dumps({"version": target.version, "tenant_id": tenant_id}),
        )
        return target

    def list_config_versions(self, tenant_id: str) -> List[ConfigurationVersion]:
        self.get_tenant(tenant_id)
        return self._configs.get(tenant_id, [])

    def get_active_configuration(self, tenant_id: str) -> TenantConfiguration:
        history = self._configs.get(tenant_id, [])
        active = next((c for c in history if c.status == ConfigVersionStatus.ACTIVE), None)
        if active:
            return active.configuration
        return TenantConfiguration()

    # -------------------------------------------------------------------------
    # Quotas & Usage
    # -------------------------------------------------------------------------

    def get_quotas(self, tenant_id: str) -> TenantQuota:
        tenant = self.get_tenant(tenant_id)
        return tenant.quotas

    def update_quotas(self, tenant_id: str, quotas: TenantQuota, actor_id: str) -> TenantQuota:
        tenant = self.get_tenant(tenant_id)
        tenant.quotas = quotas
        tenant.updated_at = datetime.now(timezone.utc)
        self._audit_service.record(
            user_id=actor_id,
            action="TENANT_QUOTAS_UPDATED",
            resource_type="TENANT",
            resource_id=tenant_id,
            new_value=json.dumps(quotas.model_dump()),
        )
        return quotas

    def get_usage_metrics(self, tenant_id: str) -> TenantUsageMetrics:
        self.get_tenant(tenant_id)
        if tenant_id not in self._usage:
            self._usage[tenant_id] = TenantUsageMetrics(tenant_id=tenant_id)
        return self._usage[tenant_id]


# Singleton instance
_global_tenancy_service: Optional[TenancyService] = None


def get_tenancy_service() -> TenancyService:
    global _global_tenancy_service
    if _global_tenancy_service is None:
        _global_tenancy_service = TenancyService()
    return _global_tenancy_service
