"""
FinGraph Kafka Dead Letter Queue (DLQ) Sink.
Routes malformed, corrupted, or unvalidated messages to the 'transactions_dlq' Kafka topic.
"""
import logging
from typing import Optional

try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None

from flink.src.config import FlinkStreamingConfig, get_flink_config
from flink.src.schemas import DLQEvent

logger = logging.getLogger("FinGraph.DLQSink")


class KafkaDLQSink:
    """
    Publishes validation failures and corrupted payloads to the designated DLQ topic.
    """

    def __init__(self, config: Optional[FlinkStreamingConfig] = None, auto_connect: bool = True):
        self.config = config or get_flink_config()
        self.topic = self.config.kafka_dlq_topic
        self.producer: Optional[KafkaProducer] = None

        if auto_connect and KafkaProducer is not None:
            self.connect()

    def connect(self) -> None:
        """Initializes KafkaProducer for DLQ routing."""
        if KafkaProducer is None:
            logger.warning("kafka-python is not installed. DLQ sink running in passive mode.")
            return

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.kafka_bootstrap_servers.split(","),
                value_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
                acks="all",
                retries=3,
            )
            logger.info(f"Connected DLQ Sink to Kafka topic '{self.topic}' at {self.config.kafka_bootstrap_servers}")
        except Exception as exc:
            logger.warning(f"Failed to connect DLQ Sink to Kafka: {exc}. Will log DLQ events to logger.")
            self.producer = None

    def publish_dlq(self, dlq_event: DLQEvent) -> None:
        """Publishes a DLQ event to Kafka topic or logs to logger if offline."""
        payload_json = dlq_event.to_json()
        logger.warning(f"[DLQ] Routing malformed record to '{self.topic}': {dlq_event.error_reason}")

        if self.producer:
            try:
                future = self.producer.send(self.topic, value=payload_json)
                future.get(timeout=5)
            except Exception as exc:
                logger.error(f"[DLQ] Failed to publish event to Kafka '{self.topic}': {exc}")
        else:
            logger.info(f"[DLQ Standalone] Stored event: {payload_json}")

    def close(self) -> None:
        """Flushes and closes the DLQ producer."""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
            except Exception:
                pass
            self.producer = None
