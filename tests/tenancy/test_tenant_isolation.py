"""
Tests for Multi-Tenant Boundary Isolation in Phase 20.
"""
import pytest
from backend.app.tenancy.models import (
    OrganizationCreateRequest,
    TeamCreateRequest,
    TenantCreateRequest,
)
from backend.app.tenancy.service import TenancyService
from backend.app.tenancy.exceptions import CrossTenantAccessError

@pytest.fixture
def service():
    return TenancyService()

def test_cross_tenant_team_access_denied(service):
    # Create Tenant A and Tenant B
    t_a = service.create_tenant(TenantCreateRequest(name="Bank Alpha", slug="bank-alpha"), actor_id="usr_plat")
    t_b = service.create_tenant(TenantCreateRequest(name="Bank Beta", slug="bank-beta"), actor_id="usr_plat")

    # Create Org & Team in Tenant A
    org_a = service.create_organization(t_a.tenant_id, OrganizationCreateRequest(name="Alpha Ops"), actor_id="usr_plat")
    team_a = service.create_team(t_a.tenant_id, TeamCreateRequest(org_id=org_a.org_id, name="Alpha Strike Squad"), actor_id="usr_plat")

    # Tenant B tries to access Tenant A team -> CrossTenantAccessError
    with pytest.raises(CrossTenantAccessError):
        service.get_team(t_b.tenant_id, team_a.team_id)
