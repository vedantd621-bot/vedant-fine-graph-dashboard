"""
FinGraph Enterprise Control Plane, Multi-Tenant Architecture & Governance REST Routes.
Provides endpoints for tenant lifecycle, organizations, teams, users, quotas, configuration versioning, policies, and tenant-scoped audit trails.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from backend.app.models.common import ApiResponse
from backend.app.policies.exceptions import PolicyNotFoundError, PolicyValidationError
from backend.app.policies.models import (
    Policy,
    PolicyCreateRequest,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    PolicyUpdateRequest,
)
from backend.app.policies.service import PolicyService, get_policy_service
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.security.dependencies import (
    require_admin,
    require_analyst,
    require_investigator,
    require_platform_admin,
    require_tenant_admin,
)
from backend.app.security.models import (
    AuditLog,
    CreateUserRequest,
    Permission,
    Role,
    UpdateUserRequest,
    User,
    UserResponse,
    UserStatusTransitionRequest,
)
from backend.app.security.user_store import UserStore, get_user_store
from backend.app.tenancy.context import TenantContext, get_tenant_context
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
    ConfigurationVersion,
    InvestigationTeam,
    Organization,
    OrganizationCreateRequest,
    TeamCreateRequest,
    TeamMemberAddRequest,
    Tenant,
    TenantConfiguration,
    TenantCreateRequest,
    TenantQuota,
    TenantStatusTransitionRequest,
    TenantUpdateRequest,
    TenantUsageMetrics,
)
from backend.app.tenancy.service import TenancyService, get_tenancy_service

logger = logging.getLogger("FinGraph.ControlPlaneRouter")

router = APIRouter(
    prefix="/api/v1/control-plane",
    tags=["Enterprise Control Plane, Multi-Tenancy & Governance"],
)


# ---------------------------------------------------------------------------
# Overview & System Health
# ---------------------------------------------------------------------------

@router.get(
    "/overview",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get control plane overview statistics",
)
def get_control_plane_overview(
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
    policy_service: PolicyService = Depends(get_policy_service),
    user_store: UserStore = Depends(get_user_store),
):
    """Returns high-level statistics for the active tenant or platform admin."""
    if ctx.is_platform_admin:
        all_tenants = tenancy_service.list_tenants()
        total_users = len(user_store.list_users())
        total_policies = len(policy_service.list_policies())
        active_tenants = sum(1 for t in all_tenants if t.status.value == "ACTIVE")
        return ApiResponse(
            data={
                "scope": "GLOBAL_PLATFORM",
                "total_tenants": len(all_tenants),
                "active_tenants": active_tenants,
                "total_users": total_users,
                "total_policies": total_policies,
                "tenant_id": ctx.tenant_id,
            }
        )

    tenant = tenancy_service.get_tenant(ctx.tenant_id)
    orgs = tenancy_service.list_organizations(ctx.tenant_id)
    teams = tenancy_service.list_teams(ctx.tenant_id)
    users = user_store.list_users(ctx.tenant_id)
    policies = policy_service.list_policies(ctx.tenant_id)
    usage = tenancy_service.get_usage_metrics(ctx.tenant_id)

    return ApiResponse(
        data={
            "scope": "TENANT",
            "tenant_id": tenant.tenant_id,
            "tenant_name": tenant.name,
            "status": tenant.status.value,
            "organization_count": len(orgs),
            "team_count": len(teams),
            "user_count": len(users),
            "policy_count": len(policies),
            "usage": usage.model_dump(),
        }
    )


# ---------------------------------------------------------------------------
# Tenant Management (Platform Admin & Tenant Admin)
# ---------------------------------------------------------------------------

@router.get(
    "/tenants",
    response_model=ApiResponse[List[Tenant]],
    summary="List enterprise tenants (Platform Admin only)",
)
def list_tenants(
    current_user: User = Depends(require_platform_admin),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    """Lists all tenant accounts across the platform."""
    tenants = tenancy_service.list_tenants()
    return ApiResponse(data=tenants)


@router.post(
    "/tenants",
    response_model=ApiResponse[Tenant],
    summary="Create a new enterprise tenant (Platform Admin only)",
)
def create_tenant(
    payload: TenantCreateRequest,
    current_user: User = Depends(require_platform_admin),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    """Provisions a new isolated tenant with baseline configuration and quotas."""
    try:
        tenant = tenancy_service.create_tenant(payload, actor_id=current_user.user_id)
        return ApiResponse(data=tenant)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/tenants/{tenant_id}",
    response_model=ApiResponse[Tenant],
    summary="Get tenant details",
)
def get_tenant_detail(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    """Fetches details for a specific tenant. Requires membership or Platform Admin."""
    if not ctx.is_in_tenant(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to other tenants is prohibited.")
    try:
        tenant = tenancy_service.get_tenant(tenant_id)
        return ApiResponse(data=tenant)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/tenants/{tenant_id}",
    response_model=ApiResponse[Tenant],
    summary="Update tenant metadata or quotas",
)
def update_tenant(
    tenant_id: str,
    payload: TenantUpdateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    """Updates tenant profile or quotas."""
    if not ctx.is_in_tenant(tenant_id) and not ctx.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    try:
        tenant = tenancy_service.update_tenant(tenant_id, payload, actor_id=ctx.user_id)
        return ApiResponse(data=tenant)
    except TenantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/tenants/{tenant_id}/status",
    response_model=ApiResponse[Tenant],
    summary="Transition tenant lifecycle status (Platform Admin only)",
)
def transition_tenant_status(
    tenant_id: str,
    payload: TenantStatusTransitionRequest,
    current_user: User = Depends(require_platform_admin),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    """Transitions tenant state: ACTIVE -> SUSPENDED -> DISABLED -> REACTIVATED."""
    try:
        tenant = tenancy_service.transition_tenant_status(tenant_id, payload, actor_id=current_user.user_id)
        return ApiResponse(data=tenant)
    except (TenantNotFoundError, InvalidTenantStateTransitionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Configuration Versioning
# ---------------------------------------------------------------------------

@router.get(
    "/tenants/{tenant_id}/configuration",
    response_model=ApiResponse[TenantConfiguration],
    summary="Get active tenant configuration",
)
def get_tenant_configuration(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if not ctx.is_in_tenant(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    config = tenancy_service.get_active_configuration(tenant_id)
    return ApiResponse(data=config)


@router.get(
    "/tenants/{tenant_id}/configuration/versions",
    response_model=ApiResponse[List[ConfigurationVersion]],
    summary="List configuration release versions",
)
def list_configuration_versions(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if not ctx.is_in_tenant(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    versions = tenancy_service.list_config_versions(tenant_id)
    return ApiResponse(data=versions)


@router.post(
    "/tenants/{tenant_id}/configuration/versions",
    response_model=ApiResponse[ConfigurationVersion],
    summary="Create draft configuration version",
)
def create_configuration_version(
    tenant_id: str,
    payload: ConfigVersionCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if not ctx.is_in_tenant(tenant_id) or ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    cfg = tenancy_service.create_config_version(tenant_id, payload, actor_id=ctx.user_id)
    return ApiResponse(data=cfg)


@router.post(
    "/tenants/{tenant_id}/configuration/{version_id}/activate",
    response_model=ApiResponse[ConfigurationVersion],
    summary="Promote configuration version to active",
)
def activate_configuration_version(
    tenant_id: str,
    version_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if not ctx.is_in_tenant(tenant_id) or ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    try:
        active_ver = tenancy_service.activate_config_version(tenant_id, version_id, actor_id=ctx.user_id)
        return ApiResponse(data=active_ver)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Quotas & Usage
# ---------------------------------------------------------------------------

@router.get(
    "/tenants/{tenant_id}/quotas",
    response_model=ApiResponse[TenantQuota],
    summary="Get tenant resource quotas",
)
def get_tenant_quotas(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if not ctx.is_in_tenant(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    quotas = tenancy_service.get_quotas(tenant_id)
    return ApiResponse(data=quotas)


@router.put(
    "/tenants/{tenant_id}/quotas",
    response_model=ApiResponse[TenantQuota],
    summary="Update tenant resource quotas (Platform Admin only)",
)
def update_tenant_quotas(
    tenant_id: str,
    quotas: TenantQuota,
    current_user: User = Depends(require_platform_admin),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    updated = tenancy_service.update_quotas(tenant_id, quotas, actor_id=current_user.user_id)
    return ApiResponse(data=updated)


@router.get(
    "/tenants/{tenant_id}/usage",
    response_model=ApiResponse[TenantUsageMetrics],
    summary="Get aggregate tenant usage metrics",
)
def get_tenant_usage(
    tenant_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if not ctx.is_in_tenant(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    usage = tenancy_service.get_usage_metrics(tenant_id)
    return ApiResponse(data=usage)


# ---------------------------------------------------------------------------
# Organization Structure & Teams
# ---------------------------------------------------------------------------

@router.get(
    "/organizations",
    response_model=ApiResponse[List[Organization]],
    summary="List organizations for current tenant",
)
def list_organizations(
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    orgs = tenancy_service.list_organizations(ctx.tenant_id)
    return ApiResponse(data=orgs)


@router.post(
    "/organizations",
    response_model=ApiResponse[Organization],
    summary="Create organization",
)
def create_organization(
    payload: OrganizationCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required.")
    org = tenancy_service.create_organization(ctx.tenant_id, payload, actor_id=ctx.user_id)
    return ApiResponse(data=org)


@router.get(
    "/business-units",
    response_model=ApiResponse[List[BusinessUnit]],
    summary="List business units",
)
def list_business_units(
    org_id: Optional[str] = Query(None),
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    units = tenancy_service.list_business_units(ctx.tenant_id, org_id=org_id)
    return ApiResponse(data=units)


@router.post(
    "/business-units",
    response_model=ApiResponse[BusinessUnit],
    summary="Create business unit",
)
def create_business_unit(
    payload: BusinessUnitCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required.")
    try:
        unit = tenancy_service.create_business_unit(ctx.tenant_id, payload, actor_id=ctx.user_id)
        return ApiResponse(data=unit)
    except OrganizationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/teams",
    response_model=ApiResponse[List[InvestigationTeam]],
    summary="List investigation teams",
)
def list_teams(
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    teams = tenancy_service.list_teams(ctx.tenant_id)
    return ApiResponse(data=teams)


@router.post(
    "/teams",
    response_model=ApiResponse[InvestigationTeam],
    summary="Create an investigation team",
)
def create_team(
    payload: TeamCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required.")
    try:
        team = tenancy_service.create_team(ctx.tenant_id, payload, actor_id=ctx.user_id)
        return ApiResponse(data=team)
    except QuotaExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/teams/{team_id}",
    response_model=ApiResponse[InvestigationTeam],
    summary="Get investigation team details",
)
def get_team_detail(
    team_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    try:
        team = tenancy_service.get_team(ctx.tenant_id, team_id)
        return ApiResponse(data=team)
    except TeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CrossTenantAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/teams/{team_id}/members",
    response_model=ApiResponse[InvestigationTeam],
    summary="Add member to team",
)
def add_team_member(
    team_id: str,
    payload: TeamMemberAddRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required.")
    try:
        team = tenancy_service.add_team_member(ctx.tenant_id, team_id, payload, actor_id=ctx.user_id)
        return ApiResponse(data=team)
    except TeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/teams/{team_id}/members/{user_id}",
    response_model=ApiResponse[InvestigationTeam],
    summary="Remove member from team",
)
def remove_team_member(
    team_id: str,
    user_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    tenancy_service: TenancyService = Depends(get_tenancy_service),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required.")
    try:
        team = tenancy_service.remove_team_member(ctx.tenant_id, team_id, user_id=user_id, actor_id=ctx.user_id)
        return ApiResponse(data=team)
    except TeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Users & Identity Lifecycle
# ---------------------------------------------------------------------------

@router.get(
    "/users",
    response_model=ApiResponse[List[UserResponse]],
    summary="List users within active tenant",
)
def list_tenant_users(
    ctx: TenantContext = Depends(get_tenant_context),
    user_store: UserStore = Depends(get_user_store),
):
    users = user_store.list_users(ctx.tenant_id if not ctx.is_platform_admin else None)
    responses = [
        UserResponse(
            user_id=u.user_id,
            username=u.username,
            role=u.role,
            is_active=u.is_active,
            tenant_id=u.tenant_id,
            organization_id=u.organization_id,
            team_ids=u.team_ids,
            permissions=u.permissions,
            created_at=u.created_at,
        )
        for u in users
    ]
    return ApiResponse(data=responses)


@router.post(
    "/users/invite",
    response_model=ApiResponse[UserResponse],
    summary="Invite or provision a new user",
)
def invite_user(
    payload: CreateUserRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    user_store: UserStore = Depends(get_user_store),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")

    target_tenant = payload.tenant_id or ctx.tenant_id
    if target_tenant != ctx.tenant_id and not ctx.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot invite user to another tenant.")

    req = CreateUserRequest(
        username=payload.username,
        password=payload.password,
        role=payload.role,
        is_active=payload.is_active,
        tenant_id=target_tenant,
        organization_id=payload.organization_id or ctx.org_id,
        team_ids=payload.team_ids or [],
        permissions=payload.permissions or [],
    )
    try:
        user = user_store.create_user(req)
        return ApiResponse(
            data=UserResponse(
                user_id=user.user_id,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                tenant_id=user.tenant_id,
                organization_id=user.organization_id,
                team_ids=user.team_ids,
                permissions=user.permissions,
                created_at=user.created_at,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/users/{user_id}/status",
    response_model=ApiResponse[UserResponse],
    summary="Update user status (ACTIVE, SUSPENDED, DISABLED)",
)
def update_user_status(
    user_id: str,
    payload: UserStatusTransitionRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    user_store: UserStore = Depends(get_user_store),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")

    user = user_store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.tenant_id != ctx.tenant_id and not ctx.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    is_active = (payload.target_status.upper() == "ACTIVE")
    user = user_store.update_user(user_id, UpdateUserRequest(is_active=is_active))
    return ApiResponse(
        data=UserResponse(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            tenant_id=user.tenant_id,
            organization_id=user.organization_id,
            team_ids=user.team_ids,
            permissions=user.permissions,
            created_at=user.created_at,
        )
    )


@router.get(
    "/roles",
    response_model=ApiResponse[List[Dict[str, Any]]],
    summary="List platform roles and default permission matrix",
)
def list_roles():
    roles = [
        {"role": "PLATFORM_ADMIN", "description": "Global platform governor with tenant lifecycle oversight"},
        {"role": "ADMIN", "description": "Tenant administrator managing users, teams, and safe policies"},
        {"role": "INVESTIGATOR", "description": "Senior investigator with case creation, evidence, and decision privileges"},
        {"role": "ANALYST", "description": "Read-only analytics and triage reviewer"},
    ]
    return ApiResponse(data=roles)


@router.get(
    "/permissions",
    response_model=ApiResponse[List[str]],
    summary="List all granular permissions",
)
def list_permissions():
    return ApiResponse(data=[p.value for p in Permission])


# ---------------------------------------------------------------------------
# Policy Engine & Authorization
# ---------------------------------------------------------------------------

@router.get(
    "/policies",
    response_model=ApiResponse[List[Policy]],
    summary="List authorization policies",
)
def list_policies(
    ctx: TenantContext = Depends(get_tenant_context),
    policy_service: PolicyService = Depends(get_policy_service),
):
    policies = policy_service.list_policies(ctx.tenant_id if not ctx.is_platform_admin else None)
    return ApiResponse(data=policies)


@router.post(
    "/policies",
    response_model=ApiResponse[Policy],
    summary="Create authorization policy",
)
def create_policy(
    payload: PolicyCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    policy_service: PolicyService = Depends(get_policy_service),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    policy = policy_service.create_policy(ctx.tenant_id, payload, actor_id=ctx.user_id)
    return ApiResponse(data=policy)


@router.get(
    "/policies/{policy_id}",
    response_model=ApiResponse[Policy],
    summary="Get policy detail",
)
def get_policy(
    policy_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    policy_service: PolicyService = Depends(get_policy_service),
):
    try:
        policy = policy_service.get_policy(policy_id)
        if policy.tenant_id != ctx.tenant_id and policy.tenant_id != "GLOBAL" and not ctx.is_platform_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return ApiResponse(data=policy)
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/policies/{policy_id}",
    response_model=ApiResponse[Policy],
    summary="Update authorization policy",
)
def update_policy(
    policy_id: str,
    payload: PolicyUpdateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    policy_service: PolicyService = Depends(get_policy_service),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required.")
    try:
        policy = policy_service.update_policy(policy_id, payload, actor_id=ctx.user_id)
        return ApiResponse(data=policy)
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/policies/{policy_id}",
    response_model=ApiResponse[bool],
    summary="Delete authorization policy",
)
def delete_policy(
    policy_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    policy_service: PolicyService = Depends(get_policy_service),
):
    if ctx.role not in [Role.ADMIN, Role.PLATFORM_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required.")
    try:
        policy_service.delete_policy(policy_id, actor_id=ctx.user_id)
        return ApiResponse(data=True)
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/policies/evaluate",
    response_model=ApiResponse[PolicyEvaluationResult],
    summary="Dry-run evaluate access against policy engine",
)
def evaluate_policy(
    payload: PolicyEvaluationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    policy_service: PolicyService = Depends(get_policy_service),
):
    result = policy_service.evaluate_access(payload)
    return ApiResponse(data=result)


# ---------------------------------------------------------------------------
# Tenant-Scoped Audit Logs
# ---------------------------------------------------------------------------

@router.get(
    "/audit",
    response_model=ApiResponse[List[AuditLog]],
    summary="Get tenant-scoped audit trail",
)
def get_tenant_audit_logs(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Returns immutable audit logs filtered by active tenant scope."""
    tenant_filter = None if ctx.is_platform_admin else ctx.tenant_id
    logs, total = audit_service.list_logs(
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        tenant_id=tenant_filter,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(data=logs)
