"""
Tests for Organization & Team Hierarchy in Phase 20.
"""
import pytest
from backend.app.tenancy.models import (
    BusinessUnitCreateRequest,
    OrganizationCreateRequest,
    TeamCreateRequest,
    TeamMemberAddRequest,
    TenantCreateRequest,
    TenantQuota,
)
from backend.app.tenancy.service import TenancyService
from backend.app.tenancy.exceptions import QuotaExceededError

@pytest.fixture
def service():
    return TenancyService()

def test_organization_and_team_crud(service):
    org = service.create_organization("tnt_default", OrganizationCreateRequest(name="Cyber Defense Org"), actor_id="usr_01")
    assert org.org_id.startswith("org_")

    unit = service.create_business_unit("tnt_default", BusinessUnitCreateRequest(org_id=org.org_id, name="Retail Fraud Unit", code="RFU"), actor_id="usr_01")
    assert unit.unit_id.startswith("unit_")

    team = service.create_team("tnt_default", TeamCreateRequest(org_id=org.org_id, name="Fast Response Squad"), actor_id="usr_01")
    assert team.team_id.startswith("team_")

    # Add member
    team = service.add_team_member("tnt_default", team.team_id, TeamMemberAddRequest(user_id="usr_inv_01", username="alice", role="LEAD"), actor_id="usr_01")
    assert len(team.members) == 1
    assert team.members[0].username == "alice"

    # Remove member
    team = service.remove_team_member("tnt_default", team.team_id, user_id="usr_inv_01", actor_id="usr_01")
    assert len(team.members) == 0

def test_team_quota_exceeded(service):
    t = service.create_tenant(TenantCreateRequest(name="Small Bank", slug="small-bank", quotas=TenantQuota(max_teams=1)), actor_id="usr_01")
    org = service.create_organization(t.tenant_id, OrganizationCreateRequest(name="Small Org"), actor_id="usr_01")

    # Team 1 (OK)
    service.create_team(t.tenant_id, TeamCreateRequest(org_id=org.org_id, name="Team 1"), actor_id="usr_01")

    # Team 2 (Quota exceeded)
    with pytest.raises(QuotaExceededError):
        service.create_team(t.tenant_id, TeamCreateRequest(org_id=org.org_id, name="Team 2"), actor_id="usr_01")
