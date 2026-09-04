"""ML Feature Generation & Feature Store Service Tests."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals
from backend.app.models.accounts import AccountDetail, AccountSummary, AccountTransactionItem
from backend.app.models.alerts import AlertSummary
from backend.app.models.features import (
    EntityFeatureVector,
    FeatureStoreExportRequest,
    FeatureStoreExportResponse,
)
from backend.app.services.feature_service import FEATURE_CATALOG, FeatureService
from detection.src.models import DetectionType, Severity


@pytest.fixture
def mock_feature_service():
    client = MagicMock()
    account_service = MagicMock()
    detection_engine = MagicMock()
    risk_engine = MagicMock()
    gds_manager = MagicMock()
    alert_service = MagicMock()
    case_service = MagicMock()

    service = FeatureService(
        client=client,
        account_service=account_service,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
        gds_manager=gds_manager,
        alert_service=alert_service,
        case_service=case_service,
    )
    return {
        "service": service,
        "account_service": account_service,
        "client": client,
        "risk_engine": risk_engine,
        "alert_service": alert_service,
        "detection_engine": detection_engine,
    }


def test_feature_catalog():
    assert len(FEATURE_CATALOG) == 18
    feature_names = [f.name for f in FEATURE_CATALOG]
    assert "pagerank" in feature_names
    assert "transaction_count_24h" in feature_names
    assert "community_size" in feature_names
    assert "detector_hit_count" in feature_names
    assert "risk_score" in feature_names


def test_extract_entity_feature_vector(mock_feature_service):
    service = mock_feature_service["service"]
    account_service = mock_feature_service["account_service"]
    alert_service = mock_feature_service["alert_service"]
    detection_engine = mock_feature_service["detection_engine"]

    now = datetime.now(timezone.utc)
    account_service.get_account_by_id.return_value = AccountDetail(
        account_id="ACC_ML_001",
        owner_id="OWN_01",
        owner_type="PERSON",
        type="CHECKING",
        balance=125000.0,
        currency="USD",
        risk_score=82.5,
        risk_level=RiskLevel.CRITICAL,
        is_frozen=False,
        features=GraphFeatures(
            account_id="ACC_ML_001",
            pagerank=0.075,
            wcc_id=1,
            louvain_community_id=8,
            in_degree=5,
            out_degree=4,
            total_degree=9,
            community_size=14,
            total_volume=350000.0,
        ),
        rule_signals=RuleSignals(
            account_id="ACC_ML_001",
            funnel_flag=True,
            one_to_many_flag=False,
            chain_flag=True,
            circular_flag=False,
            high_risk_hub_flag=True,
            layering_flag=False,
        ),
    )

    mock_txs = [
        AccountTransactionItem(transaction_id="TX_1", direction="INCOMING", counterparty="ACC_CP1", amount=50000.0, currency="USD", timestamp=now, transaction_type="transfer"),
        AccountTransactionItem(transaction_id="TX_2", direction="OUTGOING", counterparty="ACC_CP2", amount=50000.0, currency="USD", timestamp=now, transaction_type="transfer"),
    ]
    account_service.get_account_transactions.return_value = (mock_txs, 2)
    detection_engine.run_all.return_value = []
    alert_service.list_alerts.return_value = ([], 0)

    vec = service.extract_entity_features("ACC_ML_001")
    assert vec is not None
    assert vec.entity_id == "ACC_ML_001"
    assert vec.features["pagerank"] == 0.075
    assert vec.features["total_degree"] == 9.0
    assert vec.features["community_size"] == 14.0
    assert vec.features["risk_score"] == 82.5

    flat = vec.to_flat_dict()
    assert flat["entity_id"] == "ACC_ML_001"
    assert "pagerank" in flat


def test_export_feature_store_csv_and_json(mock_feature_service):
    service = mock_feature_service["service"]
    account_service = mock_feature_service["account_service"]
    alert_service = mock_feature_service["alert_service"]
    detection_engine = mock_feature_service["detection_engine"]

    now = datetime.now(timezone.utc)
    summary = AccountSummary(
        account_id="ACC_EXP_01",
        owner_id="OWN_01",
        owner_type="PERSON",
        type="CHECKING",
        risk_score=75.0,
        risk_level=RiskLevel.HIGH,
        pagerank=0.05,
        in_degree=2,
        out_degree=2,
        total_degree=4,
        louvain_community_id=6,
        total_volume=50000.0,
        is_frozen=False,
        last_activity=now,
    )
    account_service.list_accounts.return_value = ([summary], 1)
    account_service.get_account_by_id.return_value = AccountDetail(
        account_id="ACC_EXP_01",
        owner_id="OWN_01",
        owner_type="PERSON",
        type="CHECKING",
        balance=50000.0,
        currency="USD",
        risk_score=75.0,
        risk_level=RiskLevel.HIGH,
        features=GraphFeatures(account_id="ACC_EXP_01", pagerank=0.05, in_degree=2, out_degree=2, total_degree=4, community_size=6, total_volume=50000.0),
        rule_signals=RuleSignals(account_id="ACC_EXP_01"),
    )
    account_service.get_account_transactions.return_value = ([], 0)
    detection_engine.run_all.return_value = []
    alert_service.list_alerts.return_value = ([], 0)

    # 1. JSON Export
    json_req = FeatureStoreExportRequest(entity_ids=["ACC_EXP_01"], format="json")
    json_resp = service.export_features(json_req)
    assert json_resp.record_count == 1
    assert len(json_resp.data) == 1

    # 2. CSV Export
    csv_req = FeatureStoreExportRequest(entity_ids=["ACC_EXP_01"], format="csv")
    csv_resp = service.export_features(csv_req)
    assert csv_resp.record_count == 1
    assert "entity_id,timestamp,feature_version,transaction_count_1h" in csv_resp.csv_content
    assert "ACC_EXP_01" in csv_resp.csv_content
