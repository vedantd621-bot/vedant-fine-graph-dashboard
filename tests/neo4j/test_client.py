"""
Unit tests for FinGraph Neo4j Database Client.
Uses unittest.mock to verify connection management, query execution, and session handling.
"""
from unittest.mock import MagicMock, patch
import pytest

from neo4j.src.client import Neo4jClient
from neo4j.src.config import Neo4jConfig


@patch("neo4j.src.client.GraphDatabase")
def test_neo4j_client_initialization(mock_graph_db):
    """Verify Neo4jClient initializes with correct parameters and driver pooling."""
    mock_driver = MagicMock()
    mock_graph_db.driver.return_value = mock_driver

    config = Neo4jConfig(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test_password",
        database="neo4j",
        max_connection_pool_size=25,
        connection_timeout=15,
    )

    client = Neo4jClient(config=config, auto_connect=True)
    assert client.uri == "bolt://localhost:7687"
    assert client.user == "neo4j"
    assert client.driver is not None

    mock_graph_db.driver.assert_called_once_with(
        "bolt://localhost:7687",
        auth=("neo4j", "test_password"),
        max_connection_pool_size=25,
        connection_timeout=15,
    )


@patch("neo4j.src.client.GraphDatabase")
def test_neo4j_client_execute_query(mock_graph_db):
    """Verify execute_query opens session, passes parameters, and maps records to dicts."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_record1 = MagicMock()
    mock_record1.data.return_value = {"account_id": "A001", "risk_score": 75.0}

    mock_session.run.return_value = [mock_record1]
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_graph_db.driver.return_value = mock_driver

    client = Neo4jClient(auto_connect=True)
    results = client.execute_query(
        "MATCH (a:Account {account_id: $id}) RETURN a.account_id, a.risk_score",
        {"id": "A001"},
    )

    assert len(results) == 1
    assert results[0]["account_id"] == "A001"
    assert results[0]["risk_score"] == 75.0

    mock_session.run.assert_called_once_with(
        "MATCH (a:Account {account_id: $id}) RETURN a.account_id, a.risk_score",
        {"id": "A001"},
    )


@patch("neo4j.src.client.GraphDatabase")
def test_neo4j_client_execute_write(mock_graph_db):
    """Verify execute_write uses managed transaction write functions."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_tx_result = [{"created": 1}]

    # Simulate execute_write invoking callback
    def fake_execute_write(fn):
        mock_tx = MagicMock()
        mock_record = MagicMock()
        mock_record.data.return_value = {"created": 1}
        mock_tx.run.return_value = [mock_record]
        return fn(mock_tx)

    mock_session.execute_write.side_effect = fake_execute_write
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_graph_db.driver.return_value = mock_driver

    client = Neo4jClient(auto_connect=True)
    results = client.execute_write("MERGE (b:Bank {bank_id: $id})", {"id": "B01"})

    assert len(results) == 1
    assert results[0]["created"] == 1


@patch("neo4j.src.client.GraphDatabase")
def test_neo4j_client_execute_script(mock_graph_db):
    """Verify execute_script separates multiple statements and skips comments."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_session.execute_write.return_value = []
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_graph_db.driver.return_value = mock_driver

    script = """
    // First comment
    CREATE CONSTRAINT c1 IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE;
    
    // Second comment
    CREATE INDEX idx1 IF NOT EXISTS FOR (a:Account) ON (a.risk);
    """

    client = Neo4jClient(auto_connect=True)
    results = client.execute_script(script)

    assert len(results) == 2


@patch("neo4j.src.client.GraphDatabase")
def test_neo4j_client_close(mock_graph_db):
    """Verify driver is closed and cleared cleanly."""
    mock_driver = MagicMock()
    mock_graph_db.driver.return_value = mock_driver

    client = Neo4jClient(auto_connect=True)
    client.close()

    mock_driver.close.assert_called_once()
    assert client.driver is None
