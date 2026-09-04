"""
RBAC & Permission Boundary Enforcement Tests.
Verifies role separation across ANALYST, INVESTIGATOR, and ADMIN roles.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_account_service, get_alert_service, get_dashboard_service, get_neo4j_client
from backend.app.main import app
from backend.app.models.accounts import AccountDetail, AccountFreezeResponse, AccountSummary
from backend.app.models.alerts import AlertDetail, AlertSummary
from backend.app.models.dashboard import DashboardSummary, RiskDistribution
from backend.app.security.jwt import create_access_token
from detection.src.models import AlertStatus, DetectionEvidence, DetectionType, Severity
from analytics.src.models import GraphFeatures, RiskLevel, RuleSignals


def get_token_for_role(role_name: str, username: str = "test_user") -> str:
    """Helper to generate JWT tokens for specified RBAC roles."""
    return create_access_token({"sub": f"usr_{role_name.lower()}", "username": username, "role": role_name})


def test_analyst_cannot_mutate_alerts_or_freeze_accounts():
    """Verify ANALYST role is restricted from mutation actions (403 Forbidden)."""
    now = datetime.now(timezone.utc)
    mock_dash = MagicMock()
    mock_dash.get_dashboard_summary.return_value = DashboardSummary(
        total_accounts=50,
        total_transactions=200,
        total_transaction_volume=100000.0,
        open_alerts=5,
        investigating_alerts=2,
        resolved_alerts=10,
        dismissed_alerts=3,
        critical_risk_accounts=2,
        high_risk_accounts=6,
        updated_at=now,
    )
    app.dependency_overrides[get_dashboard_service] = lambda: mock_dash
    client = TestClient(app)

    try:
        analyst_token = get_token_for_role("ANALYST", "analyst")
        headers = {"Authorization": f"Bearer {analyst_token}"}

        # 1. Analyst can read dashboard
        dash_res = client.get("/api/v1/dashboard/summary", headers=headers)
        assert dash_res.status_code == 200

        # 2. Analyst CANNOT mutate alert status -> 403 Forbidden
        patch_res = client.patch(
            "/api/v1/alerts/ALT_TEST_001",
            json={"status": "INVESTIGATING"},
            headers=headers,
        )
        assert patch_res.status_code == 403
        assert patch_res.json()["error"]["code"] == "FORBIDDEN"

        # 3. Analyst CANNOT freeze account -> 403 Forbidden
        freeze_res = client.post(
            "/api/v1/accounts/A005/freeze",
            json={"freeze": True, "reason": "Unauthorized test"},
            headers=headers,
        )
        assert freeze_res.status_code == 403

        # 4. Analyst CANNOT access admin endpoints -> 403 Forbidden
        admin_res = client.get("/api/v1/admin/users", headers=headers)
        assert admin_res.status_code == 403

    finally:
        app.dependency_overrides.clear()


def test_investigator_and_admin_permissions():
    """Verify INVESTIGATOR and ADMIN can perform investigative mutations and admin actions."""
    now = datetime.now(timezone.utc)
    mock_acc_service = MagicMock()
    mock_acc_service.get_account_by_id.return_value = AccountDetail(
        account_id="A005",
        features=GraphFeatures(account_id="A005"),
        rule_signals=RuleSignals(account_id="A005"),
        is_frozen=False,
    )
    mock_acc_service.freeze_account.return_value = AccountFreezeResponse(
        account_id="A005",
        is_frozen=True,
        action="FROZEN",
        message="Account A005 frozen",
        timestamp=now,
    )
    app.dependency_overrides[get_account_service] = lambda: mock_acc_service
    client = TestClient(app)

    try:
        inv_token = get_token_for_role("INVESTIGATOR", "investigator")
        admin_token = get_token_for_role("ADMIN", "admin")

        # 1. Investigator can freeze account
        freeze_res = client.post(
            "/api/v1/accounts/A005/freeze",
            json={"freeze": True, "reason": "Forensic test freeze"},
            headers={"Authorization": f"Bearer {inv_token}"},
        )
        assert freeze_res.status_code == 200
        assert freeze_res.json()["is_frozen"] is True

        # 2. Investigator CANNOT access user administration -> 403 Forbidden
        admin_users_res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {inv_token}"})
        assert admin_users_res.status_code == 403

        # 3. Admin CAN access user administration
        admin_ok_res = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert admin_ok_res.status_code == 200
        assert isinstance(admin_ok_res.json(), list)

        # 4. Admin CAN access audit trail
        audit_res = client.get("/api/v1/admin/audit", headers={"Authorization": f"Bearer {admin_token}"})
        assert audit_res.status_code == 200
        assert "data" in audit_res.json()

    finally:
        app.dependency_overrides.clear()
