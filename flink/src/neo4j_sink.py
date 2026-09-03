"""
FinGraph Neo4j Streaming Sink.
Provides high-throughput batched upserts into Neo4j graph nodes and TRANSFERRED_TO relationships
using parameterized Cypher queries with full idempotency guarantees.
"""
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from neo4j.src.client import Neo4jClient
from neo4j.src.config import Neo4jConfig
from flink.src.config import FlinkStreamingConfig, get_flink_config
from flink.src.schemas import CanonicalTransaction

logger = logging.getLogger("FinGraph.Neo4jSink")

CYPHER_BATCH_UPSERT = """
UNWIND $batch AS event
// 1. Source Account
MERGE (src_acc:Account {account_id: event.from_account})
ON CREATE SET
    src_acc.account_type = coalesce(event.from_account_type, 'checking'),
    src_acc.risk_score = 0.0,
    src_acc.is_frozen = false

// Optional Source Person
FOREACH (_ IN CASE WHEN event.from_person_id IS NOT NULL AND event.from_person_id <> '' THEN [1] ELSE [] END |
    MERGE (p_src:Person {person_id: event.from_person_id})
    ON CREATE SET p_src.name = event.from_person_id
    MERGE (p_src)-[:OWNS]->(src_acc)
)

// Optional Source Bank
FOREACH (_ IN CASE WHEN event.from_bank_id IS NOT NULL AND event.from_bank_id <> '' THEN [1] ELSE [] END |
    MERGE (b_src:Bank {bank_id: event.from_bank_id})
    ON CREATE SET b_src.name = event.from_bank_id
    MERGE (src_acc)-[:HOSTED_BY]->(b_src)
)

// 2. Destination Account
MERGE (dst_acc:Account {account_id: event.to_account})
ON CREATE SET
    dst_acc.account_type = coalesce(event.to_account_type, 'checking'),
    dst_acc.risk_score = 0.0,
    dst_acc.is_frozen = false

// Optional Destination Person
FOREACH (_ IN CASE WHEN event.to_person_id IS NOT NULL AND event.to_person_id <> '' THEN [1] ELSE [] END |
    MERGE (p_dst:Person {person_id: event.to_person_id})
    ON CREATE SET p_dst.name = event.to_person_id
    MERGE (p_dst)-[:OWNS]->(dst_acc)
)

// Optional Destination Bank
FOREACH (_ IN CASE WHEN event.to_bank_id IS NOT NULL AND event.to_bank_id <> '' THEN [1] ELSE [] END |
    MERGE (b_dst:Bank {bank_id: event.to_bank_id})
    ON CREATE SET b_dst.name = event.to_bank_id
    MERGE (dst_acc)-[:HOSTED_BY]->(b_dst)
)

// 3. Upsert TRANSFERRED_TO relationship idempotently
MERGE (src_acc)-[r:TRANSFERRED_TO {transaction_id: event.transaction_id}]->(dst_acc)
ON CREATE SET
    r.amount = event.amount,
    r.currency = event.currency,
    r.timestamp = datetime(event.timestamp),
    r.scenario_id = event.scenario_id,
    r.transaction_type = event.transaction_type,
    r.channel = event.channel
ON MATCH SET
    r.amount = event.amount,
    r.currency = event.currency,
    r.scenario_id = event.scenario_id
"""


class Neo4jStreamingSink:
    """
    High-performance, micro-batched Neo4j graph sink for streaming transaction events.
    """

    def __init__(
        self,
        config: Optional[FlinkStreamingConfig] = None,
        client: Optional[Neo4jClient] = None,
        auto_connect: bool = True,
    ):
        self.config = config or get_flink_config()
        self.batch_size = self.config.neo4j_batch_size
        self.flush_interval_sec = self.config.neo4j_flush_interval_ms / 1000.0

        if client:
            self.client = client
            self._owns_client = False
        else:
            neo4j_cfg = Neo4jConfig(
                uri=self.config.neo4j_uri,
                user=self.config.neo4j_user,
                password=self.config.neo4j_password,
                database=self.config.neo4j_database,
            )
            try:
                self.client = Neo4jClient(config=neo4j_cfg, auto_connect=auto_connect)
            except Exception as exc:
                logger.warning(f"Neo4j client connection skipped or offline: {exc}")
                self.client = None
            self._owns_client = True

        self._buffer: List[CanonicalTransaction] = []
        self._lock = threading.Lock()
        self._last_flush_time = time.monotonic()
        self._is_closed = False

    def write_event(self, tx: CanonicalTransaction) -> None:
        """Buffers an event and flushes if batch threshold or timeout is met."""
        with self._lock:
            if self._is_closed:
                raise RuntimeError("Cannot write to closed Neo4jStreamingSink")
            self._buffer.append(tx)
            should_flush = (
                len(self._buffer) >= self.batch_size
                or (time.monotonic() - self._last_flush_time) >= self.flush_interval_sec
            )

        if should_flush:
            self.flush()

    def flush(self) -> int:
        """Executes batched Cypher write for all buffered transaction events."""
        with self._lock:
            if not self._buffer:
                self._last_flush_time = time.monotonic()
                return 0
            batch_to_write = list(self._buffer)
            self._buffer.clear()
            self._last_flush_time = time.monotonic()

        param_batch = [tx.to_neo4j_dict() for tx in batch_to_write]
        try:
            self.client.execute_write(CYPHER_BATCH_UPSERT, {"batch": param_batch})
            logger.debug(f"Successfully upserted {len(param_batch)} transactions to Neo4j.")
            return len(param_batch)
        except Exception as exc:
            logger.error(f"Failed to upsert batch of {len(param_batch)} transactions into Neo4j: {exc}")
            raise

    def close(self) -> None:
        """Flushes remaining buffered events and closes resources."""
        with self._lock:
            if self._is_closed:
                return
            self._is_closed = True

        self.flush()
        if self._owns_client and self.client:
            self.client.close()
            self.client = None

    def __enter__(self) -> "Neo4jStreamingSink":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
