"""
Tests for Quota Management & Usage Telemetry in Phase 20.
"""
import pytest
from backend.app.tenancy.models import TenantQuota
from backend.app.tenancy.service import TenancyService

@pytest.fixture
def service():
    return TenancyService()

def test_quota_update_and_usage(service):
    quotas = service.get_quotas("tnt_default")
    assert quotas.max_users >= 50

    new_quotas = TenantQuota(max_users=200, max_teams=50)
    updated = service.update_quotas("tnt_default", new_quotas, actor_id="usr_plat")
    assert updated.max_users == 200

    usage = service.get_usage_metrics("tnt_default")
    assert usage.tenant_id == "tnt_default"
    assert usage.active_users >= 1
