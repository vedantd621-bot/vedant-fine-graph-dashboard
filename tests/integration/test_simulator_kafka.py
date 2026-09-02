"""
FinGraph Simulator -> Kafka -> Consumer End-to-End Integration Test.
Verifies message streaming through Apache Kafka when a broker is available,
and validates end-to-end generator-to-consumer data integrity across all fraud topologies.
"""
import time
import uuid
from datetime import datetime, timezone
import pytest

from simulator.src.config import get_kafka_config
from simulator.src.generator import FinGraphGenerator
from simulator.src.models import (
    Currency,
    ScenarioID,
    TransactionEvent,
    TransactionType,
)


def is_kafka_broker_available(bootstrap_servers: str) -> bool:
    """Helper to detect if live Kafka cluster is reachable."""
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=[s.strip() for s in bootstrap_servers.split(",") if s.strip()],
            request_timeout_ms=1500,
            max_block_ms=1500,
        )
        producer.close()
        return True
    except Exception:
        return False


def test_simulator_to_kafka_live_integration():
    """
    Live integration test with real Kafka broker:
    1. Connects to real Kafka broker.
    2. Emits known TransactionEvent via KafkaTransactionProducer.
    3. Consumes message via KafkaConsumer.
    4. Validates payload integrity and schema.
    """
    config = get_kafka_config()
    if not is_kafka_broker_available(config.bootstrap_servers):
        pytest.skip(
            f"Live Kafka broker is not reachable at {config.bootstrap_servers}. "
            "Start Kafka (e.g. via docker-compose up -d kafka) to execute live broker integration test."
        )

    from simulator.src.kafka_producer import KafkaTransactionProducer
    from kafka import KafkaConsumer

    unique_test_id = f"TX_INT_{uuid.uuid4().hex[:8]}"
    test_topic = config.topic

    test_event = TransactionEvent(
        transaction_id=unique_test_id,
        timestamp=datetime.now(timezone.utc),
        from_account="A001",
        to_account="A010",
        amount=5432.10,
        currency=Currency.USD,
        from_person="Integration Sender",
        to_person="Integration Receiver",
        bank="B01",
        transaction_type=TransactionType.SMURFING,
        scenario_id=ScenarioID.SC_FUNNEL_01.value,
        channel="wire",
        status="COMPLETED",
        is_synthetic=True,
    )

    # 1. Produce message
    producer = KafkaTransactionProducer(config=config, auto_connect=True)
    meta = producer.publish(test_event, timeout_sec=5.0)
    producer.flush()
    producer.close()

    assert meta["topic"] == test_topic
    assert meta["transaction_id"] == unique_test_id

    # 2. Consume message
    consumer = KafkaConsumer(
        test_topic,
        bootstrap_servers=config.server_list,
        group_id=f"test-integration-consumer-{uuid.uuid4().hex[:6]}",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: m.decode("utf-8"),
        consumer_timeout_ms=5000,
    )

    received_event = None
    start_time = time.time()
    for msg in consumer:
        try:
            parsed = TransactionEvent.model_validate_json(msg.value)
            if parsed.transaction_id == unique_test_id:
                received_event = parsed
                break
        except Exception:
            continue
        if time.time() - start_time > 10:
            break

    consumer.close()

    assert received_event is not None, f"Failed to receive test transaction {unique_test_id} from Kafka topic '{test_topic}'"
    assert received_event.transaction_id == unique_test_id
    assert received_event.amount == 5432.10
    assert received_event.scenario_id == ScenarioID.SC_FUNNEL_01.value
    assert received_event.from_person == "Integration Sender"


def test_end_to_end_fraud_scenarios_pipeline_integrity():
    """
    End-to-End Pipeline Contract Test:
    Generates events for all 5 fraud syndicate topologies and verifies serialization,
    message key derivation, timestamp preservation, and schema round-trip.
    """
    gen = FinGraphGenerator(num_accounts=30, num_people=20, num_banks=3, seed=999)

    scenarios = [
        gen.generate_funnel_scenario(),
        gen.generate_distribution_scenario(),
        gen.generate_chain_scenario(),
        gen.generate_circular_scenario(),
        gen.generate_layered_network_scenario(),
    ]

    for scenario_events in scenarios:
        assert len(scenario_events) > 0
        for ev in scenario_events:
            # 1. Key derivation (transaction_id)
            key_bytes = ev.transaction_id.encode("utf-8")
            assert len(key_bytes) > 0

            # 2. Serialization to JSON
            raw_json = ev.model_dump_json()
            assert isinstance(raw_json, str)

            # 3. Deserialization & validation by consumer
            rehydrated = TransactionEvent.model_validate_json(raw_json)
            assert rehydrated.transaction_id == ev.transaction_id
            assert rehydrated.amount == ev.amount
            assert rehydrated.scenario_id == ev.scenario_id
            assert rehydrated.from_account == ev.from_account
            assert rehydrated.to_account == ev.to_account
            assert rehydrated.timestamp.tzinfo is not None
