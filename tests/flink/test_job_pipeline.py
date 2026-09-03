"""
Unit tests for FinGraph Flink Streaming Job Pipeline.
"""
import json
from unittest.mock import MagicMock
import pytest

from flink.src.job import FlinkStreamingPipeline


def test_pipeline_mixed_valid_and_invalid_stream():
    """
    Verify FlinkStreamingPipeline processes a mixed stream of valid and invalid messages:
    - Valid messages are sent to Neo4j sink.
    - Malformed messages are sent to DLQ sink.
    - Metrics accurately reflect counts.
    """
    mock_neo4j_sink = MagicMock()
    mock_dlq_sink = MagicMock()

    pipeline = FlinkStreamingPipeline(
        neo4j_sink=mock_neo4j_sink,
        dlq_sink=mock_dlq_sink,
    )

    # 1. Valid record 1
    valid_record_1 = json.dumps({
        "transaction_id": "TX_P1",
        "from_account": "A1",
        "to_account": "A2",
        "amount": 500.0,
        "currency": "USD",
        "timestamp": "2026-08-15T10:00:00Z",
        "scenario_id": "SC_NORMAL",
    })
    res1 = pipeline.process_record(valid_record_1)
    assert res1.is_valid is True
    assert mock_neo4j_sink.write_event.call_count == 1
    assert mock_dlq_sink.publish_dlq.call_count == 0

    # 2. Malformed record (negative amount)
    invalid_record_1 = json.dumps({
        "transaction_id": "TX_BAD",
        "from_account": "A1",
        "to_account": "A2",
        "amount": -50.0,
        "timestamp": "2026-08-15T10:00:00Z",
    })
    res2 = pipeline.process_record(invalid_record_1)
    assert res2.is_valid is False
    assert mock_neo4j_sink.write_event.call_count == 1
    assert mock_dlq_sink.publish_dlq.call_count == 1

    # 3. Valid record 2
    valid_record_2 = json.dumps({
        "transaction_id": "TX_P2",
        "from_account": "A2",
        "to_account": "A3",
        "amount": 750.0,
        "currency": "USD",
        "timestamp": "2026-08-15T10:05:00Z",
        "scenario_id": "SC_CIRCULAR_01",
    })
    res3 = pipeline.process_record(valid_record_2)
    assert res3.is_valid is True
    assert mock_neo4j_sink.write_event.call_count == 2
    assert mock_dlq_sink.publish_dlq.call_count == 1

    metrics = pipeline.metrics.snapshot()
    assert metrics["events_received"] == 3
    assert metrics["events_valid"] == 2
    assert metrics["events_invalid"] == 1
    assert metrics["events_written"] == 2
    assert metrics["dlq_events"] == 1
