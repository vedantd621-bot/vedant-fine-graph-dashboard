"""
FinGraph Real-Time Kafka Consumer.
Subscribes to Kafka streaming topics, deserializes transaction events, and publishes live signals to the EventBus.
"""
import asyncio
import json
import logging
import threading
import time
from typing import Any, Dict, Optional

from backend.app.config import ApiConfig, get_api_config
from backend.app.realtime.event_bus import EventBus, get_event_bus
from backend.app.realtime.events import (
    EventType,
    GraphUpdatedPayload,
    TransactionCreatedPayload,
    create_realtime_event,
)

logger = logging.getLogger("FinGraph.RealtimeKafkaConsumer")


class RealtimeKafkaConsumer:
    """Consumes transaction events from Kafka and routes them to the real-time EventBus."""

    def __init__(
        self,
        config: Optional[ApiConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.config = config or get_api_config()
        self.event_bus = event_bus or get_event_bus()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._consumer = None
        self._connected = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._processed_count = 0

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """Starts Kafka consumer polling loop in a background thread."""
        if not self.config.kafka_realtime_enabled:
            logger.info("Kafka real-time consumer is disabled in configuration.")
            return

        self._loop = loop or asyncio.get_event_loop()
        self._running = True
        self._thread = threading.Thread(target=self._run_consumer, daemon=True, name="KafkaRealtimeThread")
        self._thread.start()
        logger.info("RealtimeKafkaConsumer thread launched.")

    def stop(self) -> None:
        """Signals the background consumer thread to stop and closes the Kafka consumer."""
        self._running = False
        if self._consumer:
            try:
                self._consumer.close()
            except Exception:
                pass
        self._connected = False
        logger.info("RealtimeKafkaConsumer stopped.")

    def _run_consumer(self) -> None:
        """Internal polling loop with retry logic."""
        try:
            from kafka import KafkaConsumer
            from kafka.errors import KafkaError
        except ImportError:
            logger.warning("kafka-python not available, realtime Kafka consumer will run in simulated mode.")
            return

        retry_interval = 5.0

        while self._running:
            try:
                logger.info(f"Connecting RealtimeKafkaConsumer to {self.config.kafka_bootstrap_servers}...")
                self._consumer = KafkaConsumer(
                    self.config.kafka_topic,
                    bootstrap_servers=self.config.kafka_bootstrap_servers.split(","),
                    group_id=self.config.kafka_realtime_group,
                    auto_offset_reset="latest",
                    enable_auto_commit=True,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    consumer_timeout_ms=1000,
                )
                self._connected = True
                logger.info(f"Connected to Kafka topic '{self.config.kafka_topic}'. Consuming live events...")

                while self._running:
                    msg_pack = self._consumer.poll(timeout_ms=1000)
                    for topic_partition, messages in msg_pack.items():
                        for message in messages:
                            self._handle_message(message.value)

            except Exception as exc:
                self._connected = False
                logger.warning(f"Kafka consumer connection note: {exc}. Retrying in {retry_interval}s...")
                time.sleep(retry_interval)

    def _handle_message(self, data: Dict[str, Any]) -> None:
        """Dispatches deserialized transaction event to the async EventBus."""
        self._processed_count += 1
        tx_id = data.get("transaction_id", f"TX_{self._processed_count}")
        src = data.get("source_account", "UNKNOWN")
        dst = data.get("destination_account", "UNKNOWN")
        amount = float(data.get("amount", 0.0))
        currency = data.get("currency", "USD")
        ts_str = data.get("timestamp")
        scenario_id = data.get("scenario_id")

        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc)
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                pass

        # 1. Emit transaction.created event
        tx_payload = TransactionCreatedPayload(
            transaction_id=tx_id,
            source_account=src,
            destination_account=dst,
            amount=amount,
            currency=currency,
            timestamp=ts,
            scenario_id=scenario_id,
            channel=data.get("channel"),
        )
        tx_event = create_realtime_event(EventType.TRANSACTION_CREATED, tx_payload)

        # 2. Emit graph.updated event for source and destination accounts
        graph_payload = GraphUpdatedPayload(
            account_id=src,
            change_type="TRANSACTION_ADDED",
            related_account_id=dst,
            timestamp=ts,
        )
        graph_event = create_realtime_event(EventType.GRAPH_UPDATED, graph_payload)

        # Dispatch onto async event bus in event loop
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.event_bus.publish(tx_event), self._loop)
            asyncio.run_coroutine_threadsafe(self.event_bus.publish(graph_event), self._loop)

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def metrics(self) -> Dict[str, Any]:
        return {
            "is_connected": self._connected,
            "processed_events_count": self._processed_count,
            "topic": self.config.kafka_topic,
        }


# Global Singleton
_global_kafka_consumer: Optional[RealtimeKafkaConsumer] = None


def get_realtime_kafka_consumer() -> RealtimeKafkaConsumer:
    """Returns singleton RealtimeKafkaConsumer instance."""
    global _global_kafka_consumer
    if _global_kafka_consumer is None:
        _global_kafka_consumer = RealtimeKafkaConsumer()
    return _global_kafka_consumer
