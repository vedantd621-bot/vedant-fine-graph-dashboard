"""Behavioral Anomaly Detection and Entity Similarity Unit Tests."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals
from backend.app.models.accounts import AccountDetail, AccountSummary, AccountTransactionItem
from backend.app.models.behavior import (
    AnomalyType,
    EntityBehaviorBaseline,
    EntityBehaviorResponse,
    TemporalWindow,
)
from backend.app.services.behavior_anomaly_service import BehaviorAnomalyService


@pytest.fixture
def mock_behavior_service():
    client = MagicMock()
    account_service = MagicMock()
    detection_engine = MagicMock()
    risk_engine = MagicMock()
    event_bus = MagicMock()

    service = BehaviorAnomalyService(
        client=client,
        account_service=account_service,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
        event_bus=event_bus,
    )
    return {
        "service": service,
        "account_service": account_service,
        "client": client,
        "risk_engine": risk_engine,
    }


def test_entity_baseline_computation(mock_behavior_service):
    service = mock_behavior_service["service"]
    account_service = mock_behavior_service["account_service"]

    mock_txs = [
        AccountTransactionItem(
            transaction_id=f"TX_{i}",
            direction="OUTGOING" if i % 2 == 0 else "INCOMING",
            counterparty=f"ACC_{i}",
            amount=1000.0,
            currency="USD",
            timestamp=datetime.now(timezone.utc),
            transaction_type="transfer",
        )
        for i in range(10)
    ]
    account_service.get_account_transactions.return_value = (mock_txs, 10)

    baseline = service.get_entity_baseline("ACC_BASE_01")
    assert baseline.entity_id == "ACC_BASE_01"
    assert baseline.historical_transaction_count == 10
    assert baseline.historical_volume == 10000.0
    assert baseline.avg_transaction_amount == 1000.0
    assert baseline.unique_counterparties_count == 10


def test_volume_and_velocity_spike_detection(mock_behavior_service):
    service = mock_behavior_service["service"]
    client = mock_behavior_service["client"]
    account_service = mock_behavior_service["account_service"]

    mock_txs = [
        AccountTransactionItem(
            transaction_id=f"TX_{i}",
            direction="OUTGOING",
            counterparty=f"ACC_{i}",
            amount=500.0,
            currency="USD",
            timestamp=datetime.now(timezone.utc),
            transaction_type="transfer",
        )
        for i in range(10)
    ]
    account_service.get_account_transactions.return_value = (mock_txs, 10)

    client.execute_query.return_value = [
        {"tx_count": 25, "volume": 250000.0, "unique_dest": 12, "outgoing_vol": 240000.0, "max_amount": 50000.0}
    ]

    dossier = service.get_entity_behavior("ACC_SPIKE_01", window=TemporalWindow.WINDOW_1H)
    assert dossier.entity_id == "ACC_SPIKE_01"
    assert dossier.is_anomalous is True
    assert dossier.anomaly_score >= 50.0
    anom_types = [a.anomaly_type for a in dossier.anomalies]
    assert AnomalyType.VOLUME_SPIKE in anom_types or AnomalyType.VELOCITY_BURST in anom_types


def test_explainable_entity_similarity(mock_behavior_service):
    service = mock_behavior_service["service"]
    account_service = mock_behavior_service["account_service"]

    now = datetime.now(timezone.utc)
    target_detail = AccountDetail(
        account_id="ACC_TARGET",
        owner_id="OWN_T",
        owner_type="PERSON",
        type="CHECKING",
        balance=100000.0,
        currency="USD",
        risk_score=85.0,
        risk_level=RiskLevel.CRITICAL,
        is_frozen=False,
        features=GraphFeatures(account_id="ACC_TARGET", pagerank=0.08, in_degree=3, out_degree=3, total_degree=6, louvain_community_id=42, total_volume=100000.0),
        rule_signals=RuleSignals(account_id="ACC_TARGET"),
    )
    peer_summary = AccountSummary(
        account_id="ACC_SUSPECT_PEER",
        owner_id="OWN_P",
        owner_type="PERSON",
        type="CHECKING",
        risk_score=82.0,
        risk_level=RiskLevel.CRITICAL,
        pagerank=0.07,
        in_degree=3,
        out_degree=3,
        total_degree=6,
        louvain_community_id=42,
        total_volume=95000.0,
        is_frozen=False,
        last_activity=now,
    )

    account_service.get_account_by_id.return_value = target_detail
    account_service.list_accounts.return_value = ([peer_summary], 1)

    target_txs = [
        AccountTransactionItem(transaction_id="TX_T1", direction="OUTGOING", counterparty="CP_01", amount=5000.0, currency="USD", timestamp=now, transaction_type="transfer"),
        AccountTransactionItem(transaction_id="TX_T2", direction="OUTGOING", counterparty="CP_02", amount=5000.0, currency="USD", timestamp=now, transaction_type="transfer"),
        AccountTransactionItem(transaction_id="TX_T3", direction="OUTGOING", counterparty="CP_03", amount=5000.0, currency="USD", timestamp=now, transaction_type="transfer"),
    ]
    peer_txs = [
        AccountTransactionItem(transaction_id="TX_P1", direction="OUTGOING", counterparty="CP_01", amount=5000.0, currency="USD", timestamp=now, transaction_type="transfer"),
        AccountTransactionItem(transaction_id="TX_P2", direction="OUTGOING", counterparty="CP_02", amount=5000.0, currency="USD", timestamp=now, transaction_type="transfer"),
        AccountTransactionItem(transaction_id="TX_P3", direction="OUTGOING", counterparty="CP_99", amount=5000.0, currency="USD", timestamp=now, transaction_type="transfer"),
    ]

    account_service.get_account_transactions.side_effect = lambda account_id, page=1, page_size=50: (
        (target_txs, 3) if account_id == "ACC_TARGET" else (peer_txs, 3)
    )

    sim_resp = service.get_similar_entities("ACC_TARGET", limit=3)
    assert sim_resp.entity_id == "ACC_TARGET"
    assert len(sim_resp.similar_entities) >= 1
    top_match = sim_resp.similar_entities[0]
    assert top_match.target_entity_id == "ACC_SUSPECT_PEER"
    assert top_match.similarity_score >= 0.50
    assert "CP_01" in top_match.shared_counterparties
    assert 42 in top_match.shared_communities
