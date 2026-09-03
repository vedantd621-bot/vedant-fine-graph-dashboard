"""
Unit tests for FinGraph Kafka DLQ Sink.
"""
from unittest.mock import MagicMock, patch
import pytest

from flink.src.dlq_sink import KafkaDLQSink
from flink.src.schemas import DLQEvent


def test_dlq_sink_publish():
    """Verify DLQ sink routes event to Kafka producer."""
    dlq_event = DLQEvent(
        raw_payload='{"bad": 1}',
        error_reason="Test error",
        timestamp="2026-08-15T12:00:00Z",
    )

    sink = KafkaDLQSink(auto_connect=False)
    mock_producer = MagicMock()
    sink.producer = mock_producer

    sink.publish_dlq(dlq_event)
    mock_producer.send.assert_called_once()
    args, kwargs = mock_producer.send.call_args
    assert args[0] == sink.topic
    assert "Test error" in kwargs["value"]
