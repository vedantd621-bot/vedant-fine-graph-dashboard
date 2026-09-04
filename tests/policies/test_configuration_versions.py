"""
Tests for Immutable Configuration Versions in Phase 20.
"""
import pytest
from backend.app.tenancy.models import (
    ConfigVersionCreateRequest,
    ConfigVersionStatus,
    TenantConfiguration,
)
from backend.app.tenancy.service import TenancyService

@pytest.fixture
def service():
    return TenancyService()

def test_configuration_version_promotion(service):
    # Active config initial
    cfg1 = service.get_active_configuration("tnt_default")
    assert cfg1.default_sla_hours == 4.0

    # Create new draft version
    new_cfg = TenantConfiguration(default_sla_hours=2.0, alert_priority_threshold=80.0)
    v2 = service.create_config_version("tnt_default", ConfigVersionCreateRequest(configuration=new_cfg, release_notes="Tighter SLA"), actor_id="usr_admin")
    assert v2.status == ConfigVersionStatus.DRAFT
    assert v2.version == 2

    # Promote to active
    promoted = service.activate_config_version("tnt_default", v2.version_id, actor_id="usr_admin")
    assert promoted.status == ConfigVersionStatus.ACTIVE

    active = service.get_active_configuration("tnt_default")
    assert active.default_sla_hours == 2.0
