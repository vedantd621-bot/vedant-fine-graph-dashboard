"""
Unit tests for FinGraph Cypher Query Library.
"""
from unittest.mock import MagicMock
import pytest

from neo4j.src.queries import (
    detect_circular_flows,
    detect_distribution_patterns,
    detect_funnel_patterns,
    detect_intermediary_chains,
    get_account_counterparties,
    get_account_details,
    get_high_degree_accounts,
    get_scenario_transactions,
    trace_money_trail,
)


def test_get_account_details_query():
    """Verify get_account_details queries by account_id and returns profile."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "account_id": "A001",
        "account_type": "checking",
        "risk_score": 12.0,
        "is_frozen": False,
        "community_id": None,
        "pagerank": 0.0,
        "owner_person_id": "P001",
        "owner_name": "Alice Vance",
        "owner_country": "US",
        "bank_id": "B01",
        "bank_name": "Apex Global Bank",
        "bank_country": "US",
    }]

    details = get_account_details(mock_client, "A001")
    assert details is not None
    assert details["account_id"] == "A001"
    assert details["owner_name"] == "Alice Vance"
    mock_client.execute_query.assert_called_once()


def test_detect_circular_flows_query():
    """Verify detect_circular_flows executes cycle detection Cypher."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "cycle_nodes": ["A025", "A026", "A027", "A025"],
        "cycle_length": 3,
        "tx_ids": ["TX_CYC_001", "TX_CYC_002", "TX_CYC_003"],
        "amounts": [24000.0, 23750.0, 23500.0],
        "scenario_id": "SC_CIRCULAR_01",
    }]

    cycles = detect_circular_flows(mock_client, min_hops=2, max_hops=5)
    assert len(cycles) == 1
    assert cycles[0]["cycle_length"] == 3
    assert cycles[0]["scenario_id"] == "SC_CIRCULAR_01"


def test_detect_funnel_patterns_query():
    """Verify detect_funnel_patterns passes min_sources threshold."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "mule_account": "A005",
        "destination_account": "A006",
        "source_accounts": ["A001", "A002", "A003", "A004"],
        "source_count": 4,
        "total_inflow": 36000.0,
        "outflow_amount": 35280.0,
        "sweep_tx_id": "TX_FUN_005",
        "scenario_id": "SC_FUNNEL_01",
    }]

    funnels = detect_funnel_patterns(mock_client, min_sources=3)
    assert len(funnels) == 1
    assert funnels[0]["mule_account"] == "A005"
    assert funnels[0]["source_count"] == 4


def test_detect_distribution_patterns_query():
    """Verify detect_distribution_patterns executes fan-out detection."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "source_account": "A010",
        "destination_accounts": ["A011", "A012", "A013", "A014", "A015"],
        "destination_count": 5,
        "total_disbursed": 37500.0,
        "scenario_id": "SC_DISTRIB_01",
    }]

    distribs = detect_distribution_patterns(mock_client, min_destinations=4)
    assert len(distribs) == 1
    assert distribs[0]["source_account"] == "A010"
    assert distribs[0]["destination_count"] == 5


def test_detect_intermediary_chains_query():
    """Verify detect_intermediary_chains finds multi-hop linear paths."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "chain_nodes": ["A020", "A021", "A022", "A023", "A024"],
        "hop_count": 4,
        "amounts": [35000.0, 34300.0, 33600.0, 32900.0],
        "scenario_id": "SC_CHAIN_01",
    }]

    chains = detect_intermediary_chains(mock_client, min_hops=3, max_hops=5)
    assert len(chains) == 1
    assert chains[0]["hop_count"] == 4


def test_trace_money_trail_query():
    """Verify trace_money_trail returns path node and edge structures."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [{
        "path_nodes": [{"account_id": "A001"}, {"account_id": "A005"}, {"account_id": "A006"}],
        "path_edges": [{"transaction_id": "TX_FUN_001"}, {"transaction_id": "TX_FUN_005"}],
        "path_length": 2,
    }]

    trails = trace_money_trail(mock_client, "A001", depth=3)
    assert len(trails) == 1
    assert trails[0]["path_length"] == 2
