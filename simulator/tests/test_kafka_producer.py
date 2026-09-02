"""
Unit tests for FinGraph Kafka Producer, Consumer, and Output Sinks.
Uses unittest.mock to test Kafka integration without requiring a live Kafka cluster.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

from simulator.src.config import KafkaConfig
from simulator.src.consumer import KafkaTransactionConsumer
from simulator.src.kafka_producer import KafkaTransactionProducer
from simulator.src.models import (
    Currency,
    ScenarioID,
    TransactionEvent,
    TransactionType,
)
from simulator.src.sinks import FileSink, KafkaSink, StdoutSink, create_output_sink


@pytest.fixture
def sample_event() -> TransactionEvent:
    return TransactionEvent(
        transaction_id="TX100099",
        timestamp=datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc),
        from_account="A001",
        to_account="A002",
        amount=4500.50,
        currency=Currency.USD,
        from_person="Alice Smith",
        to_person="Bob Jones",
        bank="B01",
        transaction_type=TransactionType.TRANSFER,
        scenario_id=ScenarioID.SC_NORMAL.value,
        channel="online",
        status="COMPLETED",
        is_synthetic=True,
    )


@patch("simulator.src.kafka_producer.KafkaProducer")
def test_producer_initialization(mock_kafka_producer_cls):
    """Verify Kafka producer initializes with expected config and connects."""
    mock_instance = MagicMock()
    mock_kafka_producer_cls.return_value = mock_instance

    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        topic="transactions",
        client_id="test-producer",
        acks="all",
        retries=3,
        retry_backoff_ms=100,
    )

    producer = KafkaTransactionProducer(config=config, auto_connect=True)
    assert producer._is_connected
    assert producer.topic == "transactions"
    assert producer.bootstrap_servers == "localhost:9092"
    mock_kafka_producer_cls.assert_called_once()


@patch("simulator.src.kafka_producer.KafkaProducer")
def test_producer_publish_success(mock_kafka_producer_cls, sample_event: TransactionEvent):
    """Verify successful event publishing, key assignment, and metadata return."""
    mock_instance = MagicMock()
    mock_future = MagicMock()
    
    mock_metadata = MagicMock()
    mock_metadata.topic = "transactions"
    mock_metadata.partition = 1
    mock_metadata.offset = 42
    mock_future.get.return_value = mock_metadata
    
    mock_instance.send.return_value = mock_future
    mock_kafka_producer_cls.return_value = mock_instance

    producer = KafkaTransactionProducer(auto_connect=True)
    result = producer.publish(sample_event)

    assert result["topic"] == "transactions"
    assert result["partition"] == 1
    assert result["offset"] == 42
    assert result["transaction_id"] == "TX100099"
    assert producer.published_count == 1
    assert producer.failed_count == 0

    mock_instance.send.assert_called_once_with(
        topic="transactions",
        key="TX100099",
        value=sample_event.model_dump_json(),
    )


@patch("simulator.src.kafka_producer.KafkaProducer")
def test_producer_publish_failure(mock_kafka_producer_cls, sample_event: TransactionEvent):
    """Verify failed publishing raises exception and increments failed_count."""
    mock_instance = MagicMock()
    mock_future = MagicMock()
    mock_future.get.side_effect = TimeoutError("Kafka broker timed out")
    mock_instance.send.return_value = mock_future
    mock_kafka_producer_cls.return_value = mock_instance

    producer = KafkaTransactionProducer(auto_connect=True)
    with pytest.raises(RuntimeError, match="Kafka delivery failed"):
        producer.publish(sample_event)

    assert producer.published_count == 0
    assert producer.failed_count == 1


@patch("simulator.src.kafka_producer.KafkaProducer")
def test_producer_flush_and_close(mock_kafka_producer_cls):
    """Verify flush and close properly invoke underlying producer methods."""
    mock_instance = MagicMock()
    mock_kafka_producer_cls.return_value = mock_instance

    producer = KafkaTransactionProducer(auto_connect=True)
    producer.flush()
    mock_instance.flush.assert_called()

    producer.close()
    assert not producer._is_connected
    assert producer.producer is None
    mock_instance.close.assert_called()


def test_stdout_sink(sample_event: TransactionEvent, capsys):
    """Verify StdoutSink outputs formatted string."""
    sink = StdoutSink(quiet=False)
    sink.write(sample_event)
    captured = capsys.readouterr()
    assert "TX100099" in captured.out
    assert "A001 -> A002" in captured.out
    assert "4500.50 USD" in captured.out


def test_file_sink(tmp_path, sample_event: TransactionEvent):
    """Verify FileSink writes valid JSON lines to disk."""
    out_file = tmp_path / "test_out.jsonl"
    with FileSink(filepath=str(out_file)) as sink:
        sink.write(sample_event)

    lines = out_file.read_text().strip().splitlines()
    assert len(lines) == 1
    assert "TX100099" in lines[0]
    parsed = TransactionEvent.model_validate_json(lines[0])
    assert parsed.transaction_id == sample_event.transaction_id


@patch("simulator.src.kafka_producer.KafkaProducer")
def test_kafka_sink(mock_kafka_producer_cls, sample_event: TransactionEvent):
    """Verify KafkaSink passes events to underlying producer."""
    mock_instance = MagicMock()
    mock_future = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.topic = "transactions"
    mock_metadata.partition = 0
    mock_metadata.offset = 10
    mock_future.get.return_value = mock_metadata
    mock_instance.send.return_value = mock_future
    mock_kafka_producer_cls.return_value = mock_instance

    with KafkaSink(quiet=True) as sink:
        sink.write(sample_event)
        assert sink.producer.published_count == 1


def test_sink_factory_unsupported_spec():
    """Verify create_output_sink raises ValueError on unsupported spec."""
    with pytest.raises(ValueError, match="Unsupported output sink specification"):
        create_output_sink("unsupported_sink_protocol://")


@patch("simulator.src.consumer.KafkaConsumer")
def test_consumer_validation_and_malformed_tolerance(mock_kafka_consumer_cls, sample_event: TransactionEvent):
    """Verify Kafka consumer parses valid events and skips malformed messages without crashing."""
    valid_json = sample_event.model_dump_json()
    malformed_json_1 = '{"bad_payload": true}'  # Missing required fields
    malformed_json_2 = 'invalid json {['          # Parse error

    msg_malformed_1 = MagicMock(partition=0, offset=1, value=malformed_json_1)
    msg_malformed_2 = MagicMock(partition=0, offset=2, value=malformed_json_2)
    msg_valid = MagicMock(partition=0, offset=3, value=valid_json)

    mock_instance = MagicMock()
    mock_instance.__iter__.return_value = [msg_malformed_1, msg_malformed_2, msg_valid]
    mock_kafka_consumer_cls.return_value = mock_instance

    consumer = KafkaTransactionConsumer(
        bootstrap_servers="localhost:9092",
        topic="transactions",
    )

    stats = consumer.consume_loop(max_messages=1)
    assert stats["valid_count"] == 1
    assert stats["malformed_count"] == 2
    assert stats["total_amount"] == 4500.50
    assert stats["scenarios"][ScenarioID.SC_NORMAL.value] == 1
