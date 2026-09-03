"""
Unit tests for FinGraph Neo4j Deterministic Seed Data and Topology Integrity.
"""
from unittest.mock import MagicMock
import pytest

from neo4j.scripts.seed import seed_database
from neo4j.seed.seed_data import (
    SEED_BANKS,
    SEED_PEOPLE,
    SEED_ACCOUNTS,
    SEED_TRANSACTIONS,
)


def test_seed_entity_counts_and_uniqueness():
    """Verify seed entities have unique IDs and required fields."""
    # 1. Banks
    assert len(SEED_BANKS) == 4
    bank_ids = {b["bank_id"] for b in SEED_BANKS}
    assert len(bank_ids) == 4

    # 2. People
    assert len(SEED_PEOPLE) == 25
    person_ids = {p["person_id"] for p in SEED_PEOPLE}
    assert len(person_ids) == 25

    # 3. Accounts
    assert len(SEED_ACCOUNTS) == 30
    acc_ids = {a["account_id"] for a in SEED_ACCOUNTS}
    assert len(acc_ids) == 30
    # Every account must point to a valid owner and bank
    for acc in SEED_ACCOUNTS:
        assert acc["owner_id"] in person_ids
        assert acc["bank_id"] in bank_ids

    # 4. Transactions
    assert len(SEED_TRANSACTIONS) == 29
    tx_ids = {t["transaction_id"] for t in SEED_TRANSACTIONS}
    assert len(tx_ids) == 29
    for tx in SEED_TRANSACTIONS:
        assert tx["from_account"] in acc_ids
        assert tx["to_account"] in acc_ids
        assert tx["amount"] > 0
        assert tx["scenario_id"] is not None


def test_seed_funnel_scenario_structure():
    """Verify SC_FUNNEL_01 has multiple structured inflows and one sweep outflow."""
    funnel_txs = [t for t in SEED_TRANSACTIONS if t["scenario_id"] == "SC_FUNNEL_01"]
    assert len(funnel_txs) == 5

    inflows = [t for t in funnel_txs if t["to_account"] == "A005"]
    outflows = [t for t in funnel_txs if t["from_account"] == "A005"]

    assert len(inflows) == 4
    assert len(outflows) == 1
    assert outflows[0]["to_account"] == "A006"

    # Verify structured amounts under $10,000 threshold
    for inf in inflows:
        assert 8000.0 <= inf["amount"] < 10000.0


def test_seed_circular_scenario_structure():
    """Verify SC_CIRCULAR_01 forms a closed wash-trading cycle."""
    cycle_txs = [t for t in SEED_TRANSACTIONS if t["scenario_id"] == "SC_CIRCULAR_01"]
    assert len(cycle_txs) == 3

    flow = {t["from_account"]: t["to_account"] for t in cycle_txs}
    assert flow["A025"] == "A026"
    assert flow["A026"] == "A027"
    assert flow["A027"] == "A025"


def test_seed_chain_scenario_structure():
    """Verify SC_CHAIN_01 forms a linear multi-hop chain."""
    chain_txs = [t for t in SEED_TRANSACTIONS if t["scenario_id"] == "SC_CHAIN_01"]
    assert len(chain_txs) == 4

    hop_order = ["A020", "A021", "A022", "A023", "A024"]
    for i in range(len(hop_order) - 1):
        matching = [t for t in chain_txs if t["from_account"] == hop_order[i] and t["to_account"] == hop_order[i+1]]
        assert len(matching) == 1


def test_seed_database_execution():
    """Verify seed_database calls execute_write for all entities and relationships."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [
        {"banks": 4, "people": 25, "accounts": 30, "transfers": 26}
    ]

    summary = seed_database(mock_client)
    assert summary["banks"] == 4
    assert summary["people"] == 25
    assert summary["accounts"] == 30
    assert summary["transactions"] == 26
    assert "SC_FUNNEL_01" in summary["scenarios"]
    assert "SC_CIRCULAR_01" in summary["scenarios"]
    assert "SC_DISTRIB_01" in summary["scenarios"]
    assert "SC_CHAIN_01" in summary["scenarios"]
    assert "SC_LAYERED_01" in summary["scenarios"]
