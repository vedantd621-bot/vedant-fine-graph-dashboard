"""FastAPI REST Route Integration Tests for Phase 12."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from analytics.src.models import RiskLevel
from backend.app.dependencies import (
    get_behavior_anomaly_service,
    get_feature_service,
    get_graph_service,
    get_network_intelligence_service,
)
from backend.app.main import app
from backend.app.models.cases import CasePriority, InvestigationCase
from backend.app.models.graph import GraphPayload
from backend.app.models.networks import (
    FraudNetwork,
    FraudNetworkMember,
    NetworkDetail,
    NetworkEvidenceResponse,
    NetworkListResponse,
    NetworkMemberResponse,
    NetworkMemberRole,
    NetworkRiskExplanationResponse,
    NetworkRiskFactor,
    NetworkSummary,
    NetworkType,
)
from backend.app.models.behavior import (
    EntityBehaviorBaseline,
    EntityBehaviorResponse,
    EntitySimilarityItem,
    EntitySimilarityResponse,
    TemporalWindow,
)
from backend.app.models.features import (
    EntityFeatureVector,
    FeatureDefinition,
    FeatureStoreExportResponse,
)
from backend.app.security.jwt import create_access_token


def get_token(role: str = "INVESTIGATOR", username: str = "investigator") -> str:
    return create_access_token({"sub": f"usr_{username}", "username": username, "role": role})


@pytest.fixture
def client():
    return TestClient(app)


def test_list_and_get_network_endpoints(client):
    mock_service = MagicMock()
    now = datetime.now(timezone.utc)
    mock_summary = NetworkSummary(
        network_id="NET-001",
        name="Laundering Ring Alpha",
        network_type=NetworkType.CIRCULAR_RING,
        risk_score=88.0,
        risk_level=RiskLevel.CRITICAL,
        member_count=4,
        transaction_count=12,
        total_volume=250000.0,
        detector_count=2,
        community_id=10,
        created_at=now,
        updated_at=now,
        linked_cases_count=0,
        linked_alerts_count=1,
    )
    mock_service.list_networks.return_value = NetworkListResponse(
        data=[mock_summary],
        pagination={"page": 1, "page_size": 20, "total_items": 1, "total_pages": 1, "has_next": False, "has_prev": False},
    )
    mock_network = FraudNetwork(
        network_id="NET-001",
        name="Laundering Ring Alpha",
        network_type=NetworkType.CIRCULAR_RING,
        risk_score=88.0,
        risk_level=RiskLevel.CRITICAL,
        member_count=4,
        transaction_count=12,
        total_volume=250000.0,
        detector_count=2,
        community_id=10,
        created_at=now,
        updated_at=now,
        members=[],
        risk_factors=[],
        evidence=[],
        linked_cases=[],
        linked_alerts=[],
    )
    mock_service.get_network_by_id.return_value = NetworkDetail(network=mock_network, recent_timeline=[])

    app.dependency_overrides[get_network_intelligence_service] = lambda: mock_service

    token = get_token("ANALYST", "analyst")
    headers = {"Authorization": f"Bearer {token}"}

    list_res = client.get("/api/v1/networks", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 1
    assert list_res.json()["data"][0]["network_id"] == "NET-001"

    detail_res = client.get("/api/v1/networks/NET-001", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["network"]["network_id"] == "NET-001"

    app.dependency_overrides.clear()


def test_network_case_promotion_rbac(client):
    mock_service = MagicMock()
    mock_service.promote_network_to_case.return_value = InvestigationCase(
        case_id="CASE-NET-100",
        title="Promoted Case",
        description="Auto",
        status="OPEN",
        priority=CasePriority.HIGH,
        created_by="investigator",
    )

    app.dependency_overrides[get_network_intelligence_service] = lambda: mock_service

    analyst_token = get_token("ANALYST", "analyst")
    investigator_token = get_token("INVESTIGATOR", "investigator")

    payload = {"title": "Promoted Case", "priority": "HIGH", "description": "Auto"}

    res_analyst = client.post(
        "/api/v1/networks/NET-001/create-case",
        json=payload,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res_analyst.status_code == 403

    res_inv = client.post(
        "/api/v1/networks/NET-001/create-case",
        json=payload,
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_inv.status_code == 201
    assert res_inv.json()["case_id"] == "CASE-NET-100"

    app.dependency_overrides.clear()


def test_behavioral_endpoints(client):
    mock_service = MagicMock()
    mock_service.get_entity_behavior.return_value = EntityBehaviorResponse(
        entity_id="ACC_BEH_01",
        baseline=EntityBehaviorBaseline(entity_id="ACC_BEH_01"),
        recent_transaction_count=10,
        recent_volume=50000.0,
        active_window=TemporalWindow.WINDOW_24H,
        anomalies=[],
        anomaly_score=15.0,
        is_anomalous=False,
        summary="Normal behavior within baseline tolerances",
    )
    mock_service.get_similar_entities.return_value = EntitySimilarityResponse(
        entity_id="ACC_BEH_01",
        similar_entities=[
            EntitySimilarityItem(
                target_entity_id="ACC_BEH_02",
                similarity_score=0.85,
                shared_counterparties=["CP_1"],
                shared_communities=[5],
                shared_detectors=["FUNNEL"],
                volume_similarity=0.90,
                explanation="High counterparty and community overlap",
            )
        ],
        total_matches=1,
    )

    app.dependency_overrides[get_behavior_anomaly_service] = lambda: mock_service

    token = get_token("ANALYST", "analyst")
    headers = {"Authorization": f"Bearer {token}"}

    beh_res = client.get("/api/v1/entities/ACC_BEH_01/behavior?window=24h", headers=headers)
    assert beh_res.status_code == 200
    assert beh_res.json()["entity_id"] == "ACC_BEH_01"

    sim_res = client.get("/api/v1/entities/ACC_BEH_01/similar?top_k=3", headers=headers)
    assert sim_res.status_code == 200
    assert len(sim_res.json()["similar_entities"]) == 1

    app.dependency_overrides.clear()


def test_feature_store_endpoints(client):
    mock_service = MagicMock()
    mock_service.get_feature_catalog.return_value = [
        FeatureDefinition(name="pagerank", data_type="float", description="Centrality", source_module="gds")
    ]
    mock_service.extract_entity_features.return_value = EntityFeatureVector(
        entity_id="ACC_FEAT_01",
        features={"pagerank": 0.05, "total_degree": 5.0, "risk_score": 70.0},
    )
    mock_service.export_features.return_value = FeatureStoreExportResponse(
        feature_version="v1",
        record_count=1,
        feature_names=["pagerank"],
        csv_content="entity_id,pagerank\nACC_FEAT_01,0.05",
    )

    app.dependency_overrides[get_feature_service] = lambda: mock_service

    token = get_token("ANALYST", "analyst")
    headers = {"Authorization": f"Bearer {token}"}

    cat_res = client.get("/api/v1/features/catalog", headers=headers)
    assert cat_res.status_code == 200
    assert len(cat_res.json()) >= 1

    feat_res = client.get("/api/v1/features/entity/ACC_FEAT_01", headers=headers)
    assert feat_res.status_code == 200
    assert feat_res.json()["entity_id"] == "ACC_FEAT_01"

    exp_res = client.post("/api/v1/features/export", json={"format": "csv"}, headers=headers)
    assert exp_res.status_code == 200
    assert "entity_id,pagerank" in exp_res.json()["csv_content"]

    app.dependency_overrides.clear()
