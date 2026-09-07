"""
Master Enterprise End-to-End Pipeline Integration Test.
Validates: Early Warnings -> Risk -> Decision -> Override -> Simulation -> Analytics -> Report Snapshot -> CSV Export -> Audit.
"""
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.security.jwt import create_access_token
from backend.app.security.user_store import get_user_store


@pytest.fixture
def client():
    return TestClient(app)


def test_full_master_enterprise_pipeline_lifecycle(client):
    store = get_user_store()
    admin_user = store.get_user_by_username("admin")
    admin_token = create_access_token({
        "sub": admin_user.user_id,
        "username": admin_user.username,
        "role": admin_user.role.value,
        "tenant_id": admin_user.tenant_id,
    })
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 1: Query Detection & Early Warnings
    warnings = client.get("/api/v1/advanced-intelligence/early-warnings", headers=headers)
    assert warnings.status_code == 200

    # Step 2: Generate Deterministic Fraud Decision
    dec_res = client.post(
        "/api/v1/decisioning/",
        json={
            "entity_id": "ACC_MASTER_001",
            "risk_score": 94.5,
            "contributing_signals": ["CircularFlowDetector", "LouvainClusterBurst"],
            "evidence_summary": "High risk closed cycle detected with rapid velocity aggregation.",
        },
        headers=headers,
    )
    assert dec_res.status_code == 201
    decision = dec_res.json()
    assert decision["verdict"] == "BLOCK"
    dec_id = decision["decision_id"]

    # Step 3: Execute Human-in-the-Loop Override
    ovr_res = client.post(
        f"/api/v1/decisioning/{dec_id}/override",
        json={
            "override_verdict": "CONFIRM_FRAUD",
            "reason": "Forensic graph verification confirmed collusive syndicate ring.",
            "evidence_references": ["sha256_graph_trace_01"],
        },
        headers=headers,
    )
    assert ovr_res.status_code == 200
    assert ovr_res.json()["override_verdict"] == "CONFIRM_FRAUD"

    # Step 4: Run What-If Simulation Sandbox
    sim_res = client.post(
        "/api/v1/decisioning/simulate",
        json={
            "scenario_name": "Post-Incident Policy Tuning",
            "parameters": [
                {"name": "funnel_inflow_limit", "current_value": 10000, "hypothetical_value": 5000}
            ],
            "alert_ids": ["alt_001"],
        },
        headers=headers,
    )
    assert sim_res.status_code == 200
    assert sim_res.json()["is_production_safe"] is True

    # Step 5: Ingest into Enterprise Analytics
    analytics_res = client.get("/api/v1/analytics/kpis", headers=headers)
    assert analytics_res.status_code == 200
    bundle = analytics_res.json()
    assert bundle["posture"]["posture_score"] > 0.0

    # Step 6: Generate Immutable Audit Report Snapshot
    report_res = client.post(
        "/api/v1/reports/",
        json={
            "report_type": "EXECUTIVE_FRAUD_REPORT",
            "format": "CSV",
            "title": "Master Incident Close-Out Dossier",
        },
        headers=headers,
    )
    assert report_res.status_code == 201
    report = report_res.json()
    assert report["content_hash"] is not None
    assert len(report["content_hash"]) == 64
    report_id = report["report_id"]

    # Step 7: Export CSV with Formula Injection Neutralization
    export_res = client.get(f"/api/v1/reports/{report_id}/export?format=CSV", headers=headers)
    assert export_res.status_code == 200
    assert export_res.headers["content-type"].startswith("text/csv")
    assert "X-Content-Hash-SHA256" in export_res.headers
    assert export_res.headers["X-Content-Hash-SHA256"] == report["content_hash"]

    # Step 8: Verify Audit Trail
    audit_res = client.get("/api/v1/admin/audit", headers=headers)
    assert audit_res.status_code == 200
    res_data = audit_res.json()
    logs = res_data.get("data", [])
    actions = [l["action"] for l in logs]
    assert "DECISION_CREATED" in actions
    assert "DECISION_OVERRIDDEN" in actions
    assert "REPORT_GENERATED" in actions
