"""
Explicit Security Matrix & Cross-Tenant Safety Tests in Phase 20.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.security.jwt import create_access_token
from backend.app.security.models import Role

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def tenant_a_analyst():
    return create_access_token(payload={"sub": "usr_ana_003", "username": "analyst", "role": Role.ANALYST.value, "tenant_id": "tnt_default"})

def test_cross_tenant_header_rejection(client, tenant_a_analyst):
    # A user from tnt_default sending a header for another tenant gets 403
    headers = {
        "Authorization": f"Bearer {tenant_a_analyst}",
        "X-Tenant-ID": "tnt_foreign_bank"
    }
    res = client.get("/api/v1/control-plane/overview", headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "CROSS_TENANT_ACCESS_DENIED"
