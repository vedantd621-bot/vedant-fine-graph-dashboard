"""
FinGraph Apache Flink Streaming Pipeline Configuration.
Loads environment variables for Kafka source/DLQ topics, Neo4j sink connection,
checkpointing intervals, batching, and stream parallelism.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class FlinkStreamingConfig:
    """Configuration parameters for the Flink streaming ingestion pipeline."""
    # Kafka Source
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "transactions")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "fingraph-flink")
    kafka_auto_offset_reset: str = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")

    # Kafka Dead Letter Queue (DLQ)
    kafka_dlq_topic: str = os.getenv("KAFKA_DLQ_TOPIC", "transactions_dlq")

    # Neo4j Sink
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "fingraph_secret_pass")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    neo4j_batch_size: int = int(os.getenv("NEO4J_SINK_BATCH_SIZE", "50"))
    neo4j_flush_interval_ms: int = int(os.getenv("NEO4J_SINK_FLUSH_INTERVAL_MS", "1000"))

    # Flink Runtime Settings
    flink_parallelism: int = int(os.getenv("FLINK_PARALLELISM", "2"))
    checkpoint_interval_ms: int = int(os.getenv("FLINK_CHECKPOINT_INTERVAL_MS", "5000"))
    checkpoint_timeout_ms: int = int(os.getenv("FLINK_CHECKPOINT_TIMEOUT_MS", "10000"))


def get_flink_config() -> FlinkStreamingConfig:
    """Returns a FlinkStreamingConfig instance loaded from the active environment."""
    return FlinkStreamingConfig()
