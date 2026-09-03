"""
Unit tests for individual Cypher graph fraud detectors.
"""
from unittest.mock import MagicMock
import pytest

from detection.src.detectors.funnel import FunnelDetector
from detection.src.detectors.one_to_many import OneToManyDetector
from detection.src.detectors.chain import ChainDetector
from detection.src.detectors.circular import CircularFlowDetector, canonicalize_cycle
from detection.src.detectors.layered import LayeredNetworkDetector
from detection.src.detectors.high_degree import HighDegreeDetector
from detection.src.detectors.money_trail import MoneyTrailInvestigator
from detection.src.models import DetectionType, Severity


def test_funnel_detector():
    """Verify FunnelDetector maps Cypher records to DetectionResult."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "mule_account": "A005",
        "destination_account": "A006",
        "source_accounts": ["A001", "A002", "A003", "A004"],
        "source_count": 4,
        "total_inflow": 36000.0,
        "sweep_outflow": 35280.0,
        "tx_ids": ["TX_1", "TX_2", "TX_3", "TX_4", "TX_5"],
        "scenario_id": "SC_FUNNEL_01",
    }]

    detector = FunnelDetector(mock_client)
    results = detector.detect(min_sources=3)

    assert len(results) == 1
    res = results[0]
    assert res.detection_type == DetectionType.FUNNEL
    assert res.primary_account == "A005"
    assert res.severity == Severity.CRITICAL
    assert res.evidence.metric_value == 4
    assert res.evidence.inflow_amount == 36000.0


def test_one_to_many_detector():
    """Verify OneToManyDetector maps dispersion records."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "source_account": "A010",
        "destination_accounts": ["A011", "A012", "A013", "A014", "A015"],
        "destination_count": 5,
        "total_disbursed": 37500.0,
        "tx_ids": ["TX_D1", "TX_D2", "TX_D3", "TX_D4", "TX_D5"],
        "scenario_id": "SC_DISTRIB_01",
    }]

    detector = OneToManyDetector(mock_client)
    results = detector.detect(min_destinations=4)

    assert len(results) == 1
    assert results[0].detection_type == DetectionType.ONE_TO_MANY
    assert results[0].primary_account == "A010"
    assert results[0].evidence.metric_value == 5


def test_chain_detector():
    """Verify ChainDetector maps linear hop paths."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "chain_nodes": ["A020", "A021", "A022", "A023", "A024"],
        "hop_count": 4,
        "tx_ids": ["TX_C1", "TX_C2", "TX_C3", "TX_C4"],
        "amounts": [35000.0, 34300.0, 33600.0, 32900.0],
        "scenario_id": "SC_CHAIN_01",
    }]

    detector = ChainDetector(mock_client)
    results = detector.detect(min_depth=3, max_depth=6)

    assert len(results) == 1
    assert results[0].detection_type == DetectionType.CHAIN
    assert results[0].primary_account == "A020"
    assert results[0].evidence.hop_count == 4


def test_circular_flow_detector_and_rotational_dedup():
    """Verify CircularFlowDetector normalizes and deduplicates cycle rotations."""
    # Test canonicalize_cycle function directly
    path_rot1 = ["A026", "A027", "A025", "A026"]
    path_rot2 = ["A027", "A025", "A026", "A027"]
    c1, key1 = canonicalize_cycle(path_rot1)
    c2, key2 = canonicalize_cycle(path_rot2)
    assert c1 == ["A025", "A026", "A027", "A025"]
    assert c2 == ["A025", "A026", "A027", "A025"]
    assert key1 == key2

    mock_client = MagicMock()
    # Return two rotated copies of the same cycle
    mock_client.execute_query.return_value = [
        {
            "cycle_nodes": ["A025", "A026", "A027", "A025"],
            "cycle_length": 3,
            "tx_ids": ["TX1", "TX2", "TX3"],
            "amounts": [24000.0, 23750.0, 23500.0],
            "scenario_id": "SC_CIRCULAR_01",
        },
        {
            "cycle_nodes": ["A026", "A027", "A025", "A026"],
            "cycle_length": 3,
            "tx_ids": ["TX2", "TX3", "TX1"],
            "amounts": [23750.0, 23500.0, 24000.0],
            "scenario_id": "SC_CIRCULAR_01",
        },
    ]

    detector = CircularFlowDetector(mock_client)
    results = detector.detect()
    # Rotational dedup must collapse into exactly 1 logical cycle
    assert len(results) == 1
    assert results[0].detection_type == DetectionType.CIRCULAR_FLOW
    assert results[0].primary_account == "A025"
    assert results[0].severity == Severity.CRITICAL


def test_layered_network_detector():
    """Verify LayeredNetworkDetector identifies multi-tier aggregator structures."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "aggregator_account": "A007",
        "sources": ["A028", "A029"],
        "source_count": 2,
        "intermediaries": ["A016", "A017"],
        "intermediary_count": 2,
        "destinations": ["A008", "A009"],
        "destination_count": 2,
        "total_inflow": 18000.0,
        "tx_ids": ["TX_L1", "TX_L2", "TX_L3", "TX_L4", "TX_L5", "TX_L6"],
        "scenario_id": "SC_LAYERED_01",
    }]

    detector = LayeredNetworkDetector(mock_client)
    results = detector.detect(min_sources=2, min_intermediaries=2, min_destinations=2)

    assert len(results) == 1
    assert results[0].detection_type == DetectionType.LAYERED_NETWORK
    assert results[0].primary_account == "A007"
    assert results[0].severity == Severity.CRITICAL


def test_high_degree_detector():
    """Verify HighDegreeDetector identifies hub accounts."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "account_id": "A005",
        "account_type": "intermediary",
        "risk_score": 78.0,
        "in_degree": 4,
        "out_degree": 1,
        "total_degree": 5,
    }]

    detector = HighDegreeDetector(mock_client)
    results = detector.detect(min_degree=4)

    assert len(results) == 1
    assert results[0].detection_type == DetectionType.HIGH_DEGREE
    assert results[0].primary_account == "A005"
    assert results[0].evidence.metric_value == 5


def test_money_trail_investigator():
    """Verify MoneyTrailInvestigator returns path walks."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "path_nodes": ["A001", "A005", "A006"],
        "path_len": 2,
        "tx_ids": ["TX_FUN_001", "TX_FUN_005"],
        "amounts": [8500.0, 35280.0],
        "scenario_id": "SC_FUNNEL_01",
    }]

    investigator = MoneyTrailInvestigator(mock_client)
    results = investigator.trace(from_account="A001", to_account="A006", max_hops=3)

    assert len(results) == 1
    assert results[0].detection_type == DetectionType.MONEY_TRAIL
    assert results[0].primary_account == "A001"
    assert results[0].evidence.path_nodes == ["A001", "A005", "A006"]
