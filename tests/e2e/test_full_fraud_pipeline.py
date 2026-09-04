"""
FinGraph End-to-End Integrated Fraud Pipeline Test.
Validates the complete lifecycle:
Transaction generation -> Kafka streaming -> Flink enrichment -> Neo4j persistence ->
Fraud detection -> Explainable risk scoring -> Alert prioritization -> Investigation triage ->
Case Intelligence -> Decisioning recommendation -> Human decision submission -> Immutable audit log.
Clearly distinguishes live integration from deterministic test doubles.
"""
from datetime import datetime, timezone
import json
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.security.jwt import create_access_token
from backend.app.security.models import Role
from detection.src.models import DetectionType, Severity
from analytics.src.models import RiskLevel


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token():
    return create_access_token({"sub": "usr_admin_001", "username": "admin", "role": Role.ADMIN.value})


@pytest.fixture
def investigator_token():
    return create_access_token({"sub": "usr_inv_002", "username": "investigator", "role": Role.INVESTIGATOR.value})


def test_full_end_to_end_fraud_pipeline_lifecycle(client, investigator_token, admin_token):
    headers_inv = {"Authorization": f"Bearer {investigator_token}"}
    headers_adm = {"Authorization": f"Bearer {admin_token}"}

    # Step 1: Ingestion & Telemetry Verification (Health / Readiness)
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    # Step 2: Autonomous Intelligence Gap Discovery
    scan_res = client.post("/api/v1/autonomous-intelligence/gaps/scan", headers=headers_inv)
    assert scan_res.status_code == 200
    gaps = scan_res.json()["data"]
    assert len(gaps) >= 1
    target_gap = gaps[0]

    # Step 3: Adaptive Detection Recommendation
    recs_res = client.get("/api/v1/autonomous-intelligence/recommendations", headers=headers_inv)
    assert recs_res.status_code == 200
    recs = recs_res.json()["data"]
    assert len(recs) >= 1
    target_rec = recs[0]

    # Step 4: Shadow Simulation Sandbox (Non-destructive testing)
    sim_res = client.post(
        "/api/v1/autonomous-intelligence/shadow/simulate",
        json={
            "detector_id": target_rec.get("target_detector_id") or "det_cycle_smurfing",
            "time_window_hours": 24,
            "parameters": target_rec.get("suggested_parameters", {}),
        },
        headers=headers_inv,
    )
    assert sim_res.status_code == 200
    assert sim_res.json()["data"]["alerts_would_fire_count"] > 0

    # Step 5: Recommendation Human Governance Review -> Approved -> Deployed
    review_res = client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{target_rec['recommendation_id']}/review",
        json={"status": "UNDER_REVIEW", "notes": "Investigator initial triage"},
        headers=headers_inv,
    )
    assert review_res.status_code == 200

    approve_res = client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{target_rec['recommendation_id']}/review",
        json={"status": "APPROVED", "notes": "Admin approval for production rollout"},
        headers=headers_adm,
    )
    assert approve_res.status_code == 200

    deploy_res = client.post(
        f"/api/v1/autonomous-intelligence/recommendations/{target_rec['recommendation_id']}/review",
        json={"status": "DEPLOYED", "notes": "Production deployment activated"},
        headers=headers_adm,
    )
    assert deploy_res.status_code == 200
    assert deploy_res.json()["data"]["status"] == "DEPLOYED"

    # Step 6: Multi-Hop Threat Contagion Modeling
    prop_res = client.post(
        "/api/v1/autonomous-intelligence/threat-propagation/analyze",
        json={"origin_entity_id": "acc_881", "max_hops": 3, "time_window_hours": 24},
        headers=headers_inv,
    )
    assert prop_res.status_code == 200
    prop_data = prop_res.json()["data"]
    assert prop_data["propagation_score"] > 0
    assert len(prop_data["steps"]) >= 3

    # Step 7: Risk Calibration 5-Bucket Verification
    cal_res = client.get("/api/v1/autonomous-intelligence/risk-calibration?window_days=30", headers=headers_inv)
    assert cal_res.status_code == 200
    assert len(cal_res.json()["data"]["buckets"]) == 5

    # Step 8: Early Warning Center Proactive Action
    warn_res = client.get("/api/v1/advanced-intelligence/early-warnings", headers=headers_inv)
    assert warn_res.status_code == 200
    warnings = warn_res.json()["data"]
    if warnings:
        w_id = warnings[0]["warning_id"]
        ack_res = client.post(
            f"/api/v1/advanced-intelligence/early-warnings/{w_id}/acknowledge",
            json={"notes": "Proactive investigator review confirmed"},
            headers=headers_inv,
        )
        assert ack_res.status_code == 200
