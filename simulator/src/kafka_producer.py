"""
FinGraph Kafka Transaction Producer.
Publishes serialized TransactionEvent JSON messages to Apache Kafka with delivery confirmations,
partition keying on transaction_id, exponential retry backoff, and graceful shutdown.
"""
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from kafka import KafkaProducer
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import KafkaError, NoBrokersAvailable, TopicAlreadyExistsError
except ImportError:
    KafkaProducer = None
    KafkaAdminClient = None
    NewTopic = None
    KafkaError = Exception
    NoBrokersAvailable = Exception
    TopicAlreadyExistsError = Exception

try:
    from simulator.src.config import KafkaConfig, get_kafka_config
    from simulator.src.models import TransactionEvent
except ImportError:
    from config import KafkaConfig, get_kafka_config
    from models import TransactionEvent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [KafkaProducer] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FinGraph.KafkaProducer")


class KafkaTransactionProducer:
    """
    Production-quality Kafka Producer for streaming financial transaction events.
    """

    def __init__(
        self,
        config: Optional[KafkaConfig] = None,
        bootstrap_servers: Optional[str] = None,
        topic: Optional[str] = None,
        auto_connect: bool = True,
    ):
        self.config = config or get_kafka_config()
        self.bootstrap_servers = bootstrap_servers or self.config.bootstrap_servers
        self.topic = topic or self.config.topic
        self.producer: Optional[KafkaProducer] = None
        self._is_connected = False
        self._published_count = 0
        self._failed_count = 0

        if auto_connect:
            self.connect()

    def connect(self, max_retries: Optional[int] = None, backoff_ms: Optional[int] = None) -> None:
        """
        Establishes connection to Kafka broker with configurable retry attempts and backoff.
        """
        if KafkaProducer is None:
            raise ImportError(
                "kafka-python or kafka-python-ng is not installed. Install via requirements.txt"
            )

        retries = max_retries if max_retries is not None else self.config.retries
        backoff = (backoff_ms if backoff_ms is not None else self.config.retry_backoff_ms) / 1000.0

        for attempt in range(1, retries + 1):
            try:
                logger.info(
                    f"Connecting to Kafka at {self.bootstrap_servers} (Attempt {attempt}/{retries})..."
                )
                self.producer = KafkaProducer(
                    bootstrap_servers=self.config.server_list,
                    client_id=self.config.client_id,
                    acks=self.config.acks,
                    retries=3,
                    key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
                    value_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
                    request_timeout_ms=10000,
                    max_block_ms=10000,
                )
                self._is_connected = True
                logger.info(f"Successfully connected to Kafka cluster at {self.bootstrap_servers}")
                self._ensure_topic_exists()
                return
            except (NoBrokersAvailable, KafkaError, Exception) as exc:
                logger.warning(
                    f"Kafka connection attempt {attempt}/{retries} failed: {exc}. Retrying in {backoff:.2f}s..."
                )
                if attempt == retries:
                    logger.error(
                        f"Failed to connect to Kafka at {self.bootstrap_servers} after {retries} retries."
                    )
                    raise ConnectionError(
                        f"Could not connect to Kafka broker at {self.bootstrap_servers} after {retries} attempts: {exc}"
                    ) from exc
                time.sleep(backoff)
                backoff *= 1.5

    def _ensure_topic_exists(self, partitions: int = 3, replication_factor: int = 1) -> None:
        """Verifies or creates the target Kafka topic using KafkaAdminClient."""
        if KafkaAdminClient is None:
            return
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=self.config.server_list,
                client_id=f"{self.config.client_id}-admin",
                request_timeout_ms=5000,
            )
            existing_topics = admin.list_topics()
            if self.topic not in existing_topics:
                logger.info(
                    f"Topic '{self.topic}' does not exist. Creating topic (partitions={partitions}, replication={replication_factor})..."
                )
                new_topic = NewTopic(
                    name=self.topic,
                    num_partitions=partitions,
                    replication_factor=replication_factor,
                )
                admin.create_topics([new_topic])
                logger.info(f"Topic '{self.topic}' created successfully.")
            admin.close()
        except TopicAlreadyExistsError:
            pass
        except Exception as e:
            logger.debug(f"Topic auto-creation check skipped or not permitted: {e}")

    def publish(self, event: TransactionEvent, timeout_sec: float = 5.0) -> dict:
        """
        Publishes a validated TransactionEvent to Kafka synchronously, waiting for delivery confirmation.
        Returns metadata dict containing topic, partition, offset, and timestamp.
        """
        if not self.producer or not self._is_connected:
            raise ConnectionError("Kafka Producer is not connected. Call connect() first.")

        message_key = event.transaction_id
        message_value = event.model_dump_json()

        try:
            future = self.producer.send(
                topic=self.topic,
                key=message_key,
                value=message_value,
            )
            # Synchronous wait for broker ack
            record_metadata = future.get(timeout=timeout_sec)
            self._published_count += 1

            meta = {
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset,
                "transaction_id": event.transaction_id,
                "amount": event.amount,
                "scenario_id": event.scenario_id,
            }
            logger.debug(
                f"Published {event.transaction_id} to {meta['topic']}[{meta['partition']}] offset={meta['offset']}"
            )
            return meta

        except Exception as exc:
            self._failed_count += 1
            logger.error(f"Failed to publish transaction {event.transaction_id}: {exc}")
            raise RuntimeError(
                f"Kafka delivery failed for transaction {event.transaction_id}: {exc}"
            ) from exc

    def flush(self, timeout: Optional[float] = None) -> None:
        """Flushes any buffered records to the broker."""
        if self.producer:
            self.producer.flush(timeout=timeout)

    def close(self, timeout: Optional[float] = None) -> None:
        """Flushes and cleanly closes the producer connection."""
        if self.producer:
            logger.info("Closing Kafka producer connection...")
            try:
                self.producer.flush()
                self.producer.close(timeout=timeout)
            finally:
                self._is_connected = False
                self.producer = None
                logger.info(
                    f"Producer closed. Total published: {self._published_count}, Total failed: {self._failed_count}"
                )

    @property
    def published_count(self) -> int:
        return self._published_count

    @property
    def failed_count(self) -> int:
        return self._failed_count

    def __enter__(self) -> "KafkaTransactionProducer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
