"""
Tests for Tenant Lifecycle Management in Phase 20.
"""
import pytest
from backend.app.tenancy.models import (
    TenantCreateRequest,
    TenantStatus,
    TenantStatusTransitionRequest,
    TenantUpdateRequest,
)
from backend.app.tenancy.service import TenancyService
from backend.app.tenancy.exceptions import (
    InvalidTenantStateTransitionError,
    TenantNotFoundError,
)

@pytest.fixture
def service():
    return TenancyService()

def test_tenant_creation_and_retrieval(service):
    req = TenantCreateRequest(name="Aegis Financial", slug="aegis-fin")
    tenant = service.create_tenant(req, actor_id="usr_plat_000")
    assert tenant.tenant_id.startswith("tnt_")
    assert tenant.status == TenantStatus.ACTIVE
    assert tenant.slug == "aegis-fin"

    fetched = service.get_tenant(tenant.tenant_id)
    assert fetched.name == "Aegis Financial"
    assert fetched.active_config_version is not None

def test_duplicate_slug_rejection(service):
    req = TenantCreateRequest(name="Duplicate Bank", slug="dup-bank")
    service.create_tenant(req, actor_id="usr_plat_000")
    with pytest.raises(ValueError):
        service.create_tenant(req, actor_id="usr_plat_000")

def test_tenant_status_transitions(service):
    req = TenantCreateRequest(name="Status Test Bank", slug="status-bank")
    tenant = service.create_tenant(req, actor_id="usr_plat_000")

    # ACTIVE -> SUSPENDED
    t1 = service.transition_tenant_status(
        tenant.tenant_id,
        TenantStatusTransitionRequest(target_status=TenantStatus.SUSPENDED, reason="Audit review"),
        actor_id="usr_plat_000",
    )
    assert t1.status == TenantStatus.SUSPENDED

    # SUSPENDED -> ACTIVE (Reactivate)
    t2 = service.transition_tenant_status(
        tenant.tenant_id,
        TenantStatusTransitionRequest(target_status=TenantStatus.ACTIVE, reason="Audit cleared"),
        actor_id="usr_plat_000",
    )
    assert t2.status == TenantStatus.ACTIVE

    # ACTIVE -> DISABLED
    t3 = service.transition_tenant_status(
        tenant.tenant_id,
        TenantStatusTransitionRequest(target_status=TenantStatus.DISABLED, reason="Contract termination"),
        actor_id="usr_plat_000",
    )
    assert t3.status == TenantStatus.DISABLED

def test_invalid_status_transition(service):
    req = TenantCreateRequest(name="Illegal State Bank", slug="illegal-bank")
    tenant = service.create_tenant(req, actor_id="usr_plat_000")
    # ACTIVE -> PENDING is illegal
    with pytest.raises(InvalidTenantStateTransitionError):
        service.transition_tenant_status(
            tenant.tenant_id,
            TenantStatusTransitionRequest(target_status=TenantStatus.PENDING, reason="Illegal move"),
            actor_id="usr_plat_000",
        )

def test_tenant_not_found(service):
    with pytest.raises(TenantNotFoundError):
        service.get_tenant("tnt_non_existent")
