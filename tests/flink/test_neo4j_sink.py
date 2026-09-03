"""
Unit tests for FinGraph Neo4j Streaming Sink.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from flink.src.config import FlinkStreamingConfig
from flink.src.neo4j_sink import Neo4jStreamingSink
from flink.src.schemas import CanonicalTransaction


def test_neo4j_streaming_sink_buffering_and_flush():
    """Verify Neo4jStreamingSink buffers events and flushes batched Cypher parameters."""
    mock_client = MagicMock()
    mock_client.execute_write.return_value = [{"count": 1}]

    config = FlinkStreamingConfig(neo4j_batch_size=3, neo4j_flush_interval_ms=5000)
    sink = Neo4jStreamingSink(config=config, client=mock_client)

    tx1 = CanonicalTransaction(
        transaction_id="TX_1",
        from_account="A1",
        to_account="A2",
        amount=100.0,
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        scenario_id="SC_NORMAL",
    )
    tx2 = CanonicalTransaction(
        transaction_id="TX_2",
        from_account="A2",
        to_account="A3",
        amount=200.0,
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        scenario_id="SC_NORMAL",
    )

    sink.write_event(tx1)
    sink.write_event(tx2)
    # Batch threshold of 3 not reached yet
    assert len(sink._buffer) == 2
    mock_client.execute_write.assert_not_called()

    # Manual flush
    flushed = sink.flush()
    assert flushed == 2
    assert len(sink._buffer) == 0
    mock_client.execute_write.assert_called_once()


def test_neo4j_streaming_sink_auto_flush_on_batch_size():
    """Verify sink automatically flushes when batch_size is reached."""
    mock_client = MagicMock()
    config = FlinkStreamingConfig(neo4j_batch_size=2, neo4j_flush_interval_ms=10000)
    sink = Neo4jStreamingSink(config=config, client=mock_client)

    tx1 = CanonicalTransaction(
        transaction_id="TX_A",
        from_account="A1",
        to_account="A2",
        amount=100.0,
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        scenario_id="SC_NORMAL",
    )
    tx2 = CanonicalTransaction(
        transaction_id="TX_B",
        from_account="A2",
        to_account="A3",
        amount=200.0,
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        scenario_id="SC_NORMAL",
    )

    sink.write_event(tx1)
    assert mock_client.execute_write.call_count == 0
    sink.write_event(tx2)
    # Reached batch size 2 -> should flush
    assert mock_client.execute_write.call_count == 1
    assert len(sink._buffer) == 0


def test_neo4j_streaming_sink_close():
    """Verify sink flushes remaining items on close."""
    mock_client = MagicMock()
    config = FlinkStreamingConfig(neo4j_batch_size=10, neo4j_flush_interval_ms=10000)
    sink = Neo4jStreamingSink(config=config, client=mock_client)

    tx = CanonicalTransaction(
        transaction_id="TX_CLOSE",
        from_account="A1",
        to_account="A2",
        amount=50.0,
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        scenario_id="SC_NORMAL",
    )
    sink.write_event(tx)
    sink.close()

    assert mock_client.execute_write.call_count == 1
    assert sink._is_closed is True
