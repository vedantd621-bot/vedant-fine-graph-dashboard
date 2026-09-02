"""
FinGraph Simulator Configuration.
Loads environment variables for Kafka broker connections, topics, retry limits, and client IDs.
"""
import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class KafkaConfig:
    """Kafka client connection and operational configuration."""
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic: str = os.getenv("KAFKA_TOPIC", os.getenv("KAFKA_TOPIC_TRANSACTIONS", "transactions"))
    client_id: str = os.getenv("KAFKA_CLIENT_ID", "fingraph-simulator")
    acks: str = os.getenv("KAFKA_ACKS", "all")
    retries: int = int(os.getenv("KAFKA_RETRIES", "5"))
    retry_backoff_ms: int = int(os.getenv("KAFKA_RETRY_BACKOFF_MS", "500"))
    consumer_group: str = os.getenv("KAFKA_CONSUMER_GROUP", "fingraph-debug")
    auto_offset_reset: str = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")

    @property
    def server_list(self) -> List[str]:
        return [s.strip() for s in self.bootstrap_servers.split(",") if s.strip()]


def get_kafka_config() -> KafkaConfig:
    return KafkaConfig()
