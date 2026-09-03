"""
Live Integration Tests for Neo4j Database.
Executes schema initialization, database seeding, and real-time Cypher fraud detection queries
when a live Neo4j cluster is reachable at bolt://localhost:7687.
"""
import time
import pytest

from neo4j.src.client import Neo4jClient
from neo4j.src.config import get_neo4j_config
from neo4j.scripts.init_schema import apply_schema
from neo4j.scripts.seed import seed_database
from neo4j.src.queries import (
    detect_circular_flows,
    detect_distribution_patterns,
    detect_funnel_patterns,
    detect_intermediary_chains,
    get_account_details,
)


def is_live_neo4j_available() -> bool:
    """Helper to detect if live Neo4j database is reachable."""
    config = get_neo4j_config()
    try:
        with Neo4jClient(config=config, auto_connect=True) as client:
            return client.verify_connectivity()
    except Exception:
        return False


def test_live_neo4j_schema_seed_and_fraud_queries():
    """
    Live Neo4j Integration Test:
    1. Verifies connectivity to live Neo4j instance.
    2. Applies constraints and indexes.
    3. Seeds deterministic graph data.
    4. Executes live Cypher fraud queries and asserts exact syndicate pattern discovery.
    """
    if not is_live_neo4j_available():
        pytest.skip(
            "Live Neo4j database is not reachable at bolt://localhost:7687. "
            "Start Neo4j (e.g. via docker-compose up -d neo4j) to execute live graph integration tests."
        )

    config = get_neo4j_config()
    with Neo4jClient(config=config, auto_connect=True) as client:
        # 1. Apply Schema
        schema_summary = apply_schema(client)
        assert schema_summary["constraints_applied"] >= 1
        assert schema_summary["indexes_applied"] >= 1

        # 2. Seed Database
        seed_summary = seed_database(client)
        assert seed_summary["banks"] >= 4
        assert seed_summary["people"] >= 25
        assert seed_summary["accounts"] >= 30
        assert seed_summary["transactions"] >= 26

        # 3. Live Account Lookup Query
        t0 = time.perf_counter()
        acc_a001 = get_account_details(client, "A001")
        t_lookup_ms = (time.perf_counter() - t0) * 1000
        assert acc_a001 is not None
        assert acc_a001["account_id"] == "A001"
        assert acc_a001["bank_name"] == "Apex Global Bank"

        # 4. Live Funnel Detection Query
        funnels = detect_funnel_patterns(client, min_sources=3)
        assert len(funnels) >= 1
        f_match = [f for f in funnels if f["mule_account"] == "A005"]
        assert len(f_match) == 1
        assert f_match[0]["destination_account"] == "A006"
        assert f_match[0]["source_count"] == 4

        # 5. Live Circular Flow Detection Query
        cycles = detect_circular_flows(client, min_hops=2, max_hops=5)
        assert len(cycles) >= 1
        c_match = [c for c in cycles if c["scenario_id"] == "SC_CIRCULAR_01"]
        assert len(c_match) >= 1
        assert c_match[0]["cycle_length"] == 3

        # 6. Live Distribution Detection Query
        distribs = detect_distribution_patterns(client, min_destinations=4)
        assert len(distribs) >= 1
        d_match = [d for d in distribs if d["source_account"] == "A010"]
        assert len(d_match) == 1
        assert d_match[0]["destination_count"] == 5

        # 7. Live Chain Detection Query
        chains = detect_intermediary_chains(client, min_hops=3, max_hops=5)
        assert len(chains) >= 1
        ch_match = [ch for ch in chains if ch["scenario_id"] == "SC_CHAIN_01"]
        assert len(ch_match) >= 1
        assert ch_match[0]["hop_count"] == 4
