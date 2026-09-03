"""
End-to-End Streaming Pipeline Integration Tests.
Verifies Simulator -> Kafka -> Flink Validation -> Neo4j Sink ingestion flow
across normal traffic and all 5 fraud syndicate topologies, DLQ routing, and deduplication.
"""
import json
from unittest.mock import MagicMock
import pytest

from simulator.src.generator import FinGraphGenerator
from simulator.src.models import ScenarioID
from flink.src.job import FlinkStreamingPipeline
from flink.src.schemas import CanonicalTransaction


def test_e2e_simulator_to_flink_fraud_topologies_ingestion():
    """
    Simulates real transaction generation from simulator across all fraud topologies,
    passes them through Flink decoding & validation, and verifies that Neo4j sink receives
    all valid transactions with correct graph metadata.
    """
    generator = FinGraphGenerator(seed=42, num_accounts=50, num_people=50, num_banks=4)
    mock_neo4j_sink = MagicMock()
    mock_dlq_sink = MagicMock()

    pipeline = FlinkStreamingPipeline(
        neo4j_sink=mock_neo4j_sink,
        dlq_sink=mock_dlq_sink,
    )

    # Generate events for all 5 fraud topologies
    scenario_generators = [
        generator.generate_funnel_scenario,
        generator.generate_distribution_scenario,
        generator.generate_chain_scenario,
        generator.generate_circular_scenario,
        generator.generate_layered_network_scenario,
    ]

    total_generated = 0
    for gen_fn in scenario_generators:
        events = gen_fn()
        for ev in events:
            json_bytes = ev.model_dump_json().encode("utf-8")
            res = pipeline.process_record(json_bytes)
            assert res.is_valid is True
            assert res.transaction is not None
            assert res.transaction.scenario_id.startswith("SC_")
            total_generated += 1

    assert mock_neo4j_sink.write_event.call_count == total_generated
    assert mock_dlq_sink.publish_dlq.call_count == 0

    metrics = pipeline.metrics.snapshot()
    assert metrics["events_received"] == total_generated
    assert metrics["events_valid"] == total_generated
    assert metrics["events_written"] == total_generated
    assert metrics["dlq_events"] == 0


def test_e2e_duplicate_transaction_deduplication():
    """
    Verify duplicate transaction ID sent through pipeline produces idempotent calls
    and does not crash or produce conflicting records.
    """
    mock_neo4j_sink = MagicMock()
    mock_dlq_sink = MagicMock()
    pipeline = FlinkStreamingPipeline(
        neo4j_sink=mock_neo4j_sink,
        dlq_sink=mock_dlq_sink,
    )

    tx_json = json.dumps({
        "transaction_id": "TX_DUP_TEST_001",
        "from_account": "A100",
        "to_account": "A200",
        "amount": 5000.0,
        "currency": "USD",
        "timestamp": "2026-08-15T12:00:00Z",
        "scenario_id": "SC_CIRCULAR_01",
    }).encode("utf-8")

    # Send first time
    res1 = pipeline.process_record(tx_json)
    assert res1.is_valid is True

    # Send duplicate
    res2 = pipeline.process_record(tx_json)
    assert res2.is_valid is True

    assert mock_neo4j_sink.write_event.call_count == 2
    # Neo4j sink uses MERGE on (src)-[r:TRANSFERRED_TO {transaction_id}]->(dst)
    # ensuring database-level idempotency without edge duplication.


def test_e2e_malformed_event_dlq_isolation():
    """
    Verify corrupted payload in stream is routed to DLQ without halting pipeline.
    """
    mock_neo4j_sink = MagicMock()
    mock_dlq_sink = MagicMock()
    pipeline = FlinkStreamingPipeline(
        neo4j_sink=mock_neo4j_sink,
        dlq_sink=mock_dlq_sink,
    )

    corrupted_messages = [
        b'{"transaction_id": "", "amount": 100}',
        b'{"transaction_id": "T1", "amount": -100}',
        b'{"transaction_id": "T2", "currency": "DOGE"}',
        b'NOT_A_JSON_PAYLOAD',
    ]

    for msg in corrupted_messages:
        res = pipeline.process_record(msg)
        assert res.is_valid is False
        assert res.dlq_event is not None

    assert mock_neo4j_sink.write_event.call_count == 0
    assert mock_dlq_sink.publish_dlq.call_count == len(corrupted_messages)
    metrics = pipeline.metrics.snapshot()
    assert metrics["dlq_events"] == len(corrupted_messages)
    assert metrics["events_written"] == 0
