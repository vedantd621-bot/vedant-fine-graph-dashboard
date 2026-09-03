"""
Unit tests for FinGraph Neo4j Schema, Constraints, and Indexes.
"""
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from neo4j.scripts.init_schema import apply_schema


def test_schema_cypher_files_exist():
    """Verify constraint and index cypher files exist and contain valid cypher."""
    root = Path(__file__).resolve().parent.parent.parent
    constraints_path = root / "neo4j" / "constraints" / "schema.cypher"
    indexes_path = root / "neo4j" / "indexes" / "indexes.cypher"

    assert constraints_path.is_file(), "schema.cypher constraints file missing"
    assert indexes_path.is_file(), "indexes.cypher file missing"

    c_text = constraints_path.read_text(encoding="utf-8")
    assert "CREATE CONSTRAINT c_account_id_unique" in c_text
    assert "CREATE CONSTRAINT c_person_id_unique" in c_text
    assert "CREATE CONSTRAINT c_bank_id_unique" in c_text
    assert "IF NOT EXISTS" in c_text

    i_text = indexes_path.read_text(encoding="utf-8")
    assert "idx_account_risk_score" in i_text
    assert "idx_account_community_id" in i_text
    assert "idx_rel_transferred_timestamp" in i_text
    assert "idx_rel_transferred_scenario" in i_text
    assert "idx_rel_transferred_tx_id" in i_text


def test_apply_schema_idempotency():
    """Verify apply_schema parses scripts and calls execute_script on client."""
    mock_client = MagicMock()
    mock_client.execute_script.return_value = [{"result": "ok"}]
    mock_client.execute_query.side_effect = [
        [{"name": "c_account_id_unique"}, {"name": "c_person_id_unique"}, {"name": "c_bank_id_unique"}],
        [{"name": "idx_account_risk_score"}, {"name": "idx_account_community_id"}],
    ]

    summary = apply_schema(mock_client)
    assert summary["constraints_applied"] == 1
    assert summary["indexes_applied"] == 1
    assert summary["total_active_constraints"] == 3
    assert summary["total_active_indexes"] == 2
    assert mock_client.execute_script.call_count == 2
