"""
Entity Risk Profile & Explainable Risk Analysis Unit Tests.
Verifies multi-dimensional entity dossiers, ranked explainable factors, and evidence references.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals
from backend.app.dependencies import get_intelligence_service, get_neo4j_client, get_risk_engine
from backend.app.main import app
from backend.app.models.accounts import AccountDetail
from backend.app.models.intelligence import (
    EntityRiskProfile,
    EntityType,
    ExplainableRiskFactor,
    RiskExplanationResponse,
)
from backend.app.security.jwt import create_access_token
from detection.src.models import Severity


@pytest.fixture
def client():
    return TestClient(app)


def test_entity_risk_profile_endpoint(client):
    """Verify GET /api/v1/entities/{id}/risk-profile returns rich multi-signal risk profile."""
    mock_intel_service = MagicMock()
    mock_intel_service.get_entity_risk_profile.return_value = EntityRiskProfile(
        entity_id="A001",
        entity_type=EntityType.ACCOUNT,
        name="John Doe",
        risk_score=88.5,
        risk_level=RiskLevel.CRITICAL,
        major_risk_factors=[
            ExplainableRiskFactor(
                factor_type="DETECTOR_CIRCULAR_FLOW",
                description="Account participates in a 4-node closed wash trading loop.",
                severity=Severity.CRITICAL,
                weight=3.5,
                evidence_reference="FINGERPRINT_CIRC_001",
                value={"pattern": "CIRCULAR_FLOW"},
            ),
            ExplainableRiskFactor(
                factor_type="HIGH_PAGERANK_CENTRALITY",
                description="Elevated PageRank centrality (0.750) identifies account as a structural liquidity transit hub.",
                severity=Severity.HIGH,
                weight=2.0,
                evidence_reference="GDS_PAGERANK",
                value=0.75,
            ),
        ],
        detector_hits=["CIRCULAR_FLOW", "HIGH_DEGREE"],
        graph_metrics={"pagerank": 0.75, "community_id": 1, "total_degree": 6},
        connected_suspicious_entities=[{"account_id": "A002", "risk_score": 85.0, "risk_level": "CRITICAL"}],
        recent_suspicious_activity=[{"transaction_id": "TX_001", "amount": 50000.0}],
        investigation_history=[{"case_id": "CASE-001", "status": "IN_PROGRESS"}],
        is_frozen=False,
    )

    app.dependency_overrides[get_intelligence_service] = lambda: mock_intel_service
    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        res = client.get("/api/v1/entities/A001/risk-profile", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["entity_id"] == "A001"
        assert data["risk_score"] == 88.5
        assert data["risk_level"] == "CRITICAL"
        assert len(data["major_risk_factors"]) == 2
        assert data["major_risk_factors"][0]["factor_type"] == "DETECTOR_CIRCULAR_FLOW"
        assert len(data["detector_hits"]) == 2
        assert len(data["connected_suspicious_entities"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_entity_risk_explanation_endpoint(client):
    """Verify GET /api/v1/entities/{id}/risk-explanation returns explainable factors and summary."""
    mock_intel_service = MagicMock()
    mock_intel_service.get_risk_explanation.return_value = RiskExplanationResponse(
        entity_id="A001",
        entity_type=EntityType.ACCOUNT,
        risk_score=88.5,
        risk_level=RiskLevel.CRITICAL,
        reasons=[
            ExplainableRiskFactor(
                factor_type="DETECTOR_CIRCULAR_FLOW",
                description="Account participates in a 4-node closed wash trading loop.",
                severity=Severity.CRITICAL,
                weight=3.5,
                evidence_reference="FINGERPRINT_CIRC_001",
            )
        ],
        summary="Account 'A001' carries a CRITICAL risk score of 88.5 driven by 1 identified topological risk factor.",
    )

    app.dependency_overrides[get_intelligence_service] = lambda: mock_intel_service
    try:
        token = create_access_token({"sub": "usr_analyst", "username": "analyst", "role": "ANALYST"})
        res = client.get("/api/v1/entities/A001/risk-explanation", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["entity_id"] == "A001"
        assert data["risk_score"] == 88.5
        assert len(data["reasons"]) == 1
        assert "CRITICAL" in data["summary"]
    finally:
        app.dependency_overrides.clear()
