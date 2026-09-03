#!/usr/bin/env python3
"""
FinGraph Apache Flink Streaming Pipeline Runner.
Consumes transaction events from Kafka, validates & normalizes schemas,
persists graph entities & relationships to Neo4j, and routes malformed payloads to DLQ.
"""
import argparse
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from kafka import KafkaConsumer
except ImportError:
    KafkaConsumer = None

from flink.src.config import FlinkStreamingConfig, get_flink_config
from flink.src.schemas import CanonicalTransaction, DLQEvent, ValidationResult
from flink.src.transforms import decode_and_validate
from flink.src.neo4j_sink import Neo4jStreamingSink
from flink.src.dlq_sink import KafkaDLQSink
from flink.src.metrics import StreamingMetrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [FlinkJob] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FinGraph.FlinkJob")


class FlinkStreamingPipeline:
    """
    Streaming pipeline execution coordinator.
    Connects Kafka source -> Validation Transform -> Neo4j Sink & DLQ Sink.
    """

    def __init__(
        self,
        config: Optional[FlinkStreamingConfig] = None,
        neo4j_sink: Optional[Neo4jStreamingSink] = None,
        dlq_sink: Optional[KafkaDLQSink] = None,
    ):
        self.config = config or get_flink_config()
        self.neo4j_sink = neo4j_sink or Neo4jStreamingSink(config=self.config)
        self.dlq_sink = dlq_sink or KafkaDLQSink(config=self.config)
        self.metrics = StreamingMetrics()
        self.running = True

    def process_record(
        self,
        raw_val: bytes | str,
        topic: str = "transactions",
        partition: int = 0,
        offset: int = 0,
    ) -> ValidationResult:
        """
        Executes single-record stream pipeline transformation.
        Routes to Neo4j sink or DLQ sink based on validation result.
        """
        self.metrics.record_received()

        val_result = decode_and_validate(
            raw_input=raw_val,
            topic=topic,
            partition=partition,
            offset=offset,
        )

        if val_result.is_valid and val_result.transaction:
            self.metrics.record_valid()
            try:
                self.neo4j_sink.write_event(val_result.transaction)
                self.metrics.record_written()
            except Exception as exc:
                self.metrics.record_failed()
                logger.error(f"Failed writing event {val_result.transaction.transaction_id} to Neo4j: {exc}")
        else:
            self.metrics.record_invalid()
            if val_result.dlq_event:
                self.dlq_sink.publish_dlq(val_result.dlq_event)

        return val_result

    def run_consumer_loop(self, max_messages: Optional[int] = None) -> None:
        """
        Runs the real-time Kafka consumer streaming loop.
        """
        if KafkaConsumer is None:
            raise ImportError("kafka-python is required to run the Kafka streaming consumer loop.")

        logger.info(
            f"Starting Flink streaming consumer for topic '{self.config.kafka_topic}' "
            f"on {self.config.kafka_bootstrap_servers} (Group: {self.config.kafka_group_id})..."
        )

        consumer = KafkaConsumer(
            self.config.kafka_topic,
            bootstrap_servers=self.config.kafka_bootstrap_servers.split(","),
            group_id=self.config.kafka_group_id,
            auto_offset_reset=self.config.kafka_auto_offset_reset,
            enable_auto_commit=True,
            consumer_timeout_ms=1000,
        )

        msg_count = 0
        try:
            while self.running:
                records = consumer.poll(timeout_ms=500)
                for topic_partition, record_list in records.items():
                    for record in record_list:
                        self.process_record(
                            raw_val=record.value,
                            topic=record.topic,
                            partition=record.partition,
                            offset=record.offset,
                        )
                        msg_count += 1
                        if max_messages and msg_count >= max_messages:
                            logger.info(f"Reached max_messages limit ({max_messages}). Stopping.")
                            self.running = False
                            break
                    if not self.running:
                        break

                # Periodic sink flush
                self.neo4j_sink.flush()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal. Stopping Flink stream processing...")
        finally:
            consumer.close()
            self.close()

    def close(self) -> None:
        """Closes all sinks and flushes buffers."""
        self.running = False
        if self.neo4j_sink:
            self.neo4j_sink.close()
        if self.dlq_sink:
            self.dlq_sink.close()
        logger.info(f"Flink Pipeline Stopped. Final Metrics: {self.metrics.snapshot()}")


def main():
    parser = argparse.ArgumentParser(description="FinGraph Apache Flink Streaming Pipeline Runner")
    parser.add_argument("--bootstrap-servers", default=None, help="Kafka bootstrap servers")
    parser.add_argument("--topic", default=None, help="Input Kafka topic")
    parser.add_argument("--dlq-topic", default=None, help="DLQ Kafka topic")
    parser.add_argument("--group-id", default=None, help="Kafka consumer group ID")
    parser.add_argument("--max-messages", type=int, default=None, help="Stop after N messages")
    parser.add_argument("--dry-run", action="store_true", help="Run without live external connections")
    args = parser.parse_args()

    config = get_flink_config()
    print("=" * 70)
    print("  FinGraph Apache Flink Streaming Pipeline")
    print("=" * 70)
    print(f"  Kafka Source:     {config.kafka_bootstrap_servers} (Topic: {config.kafka_topic})")
    print(f"  DLQ Topic:        {config.kafka_dlq_topic}")
    print(f"  Neo4j Sink:       {config.neo4j_uri} (Database: {config.neo4j_database})")
    print(f"  Batch Size:       {config.neo4j_batch_size}")
    print(f"  Flush Interval:   {config.neo4j_flush_interval_ms} ms")
    print("=" * 70)

    if args.dry_run:
        print("[*] Dry run mode enabled. Validating pipeline modules...")
        neo4j_sink = Neo4jStreamingSink(config=config, auto_connect=False)
        dlq_sink = KafkaDLQSink(config=config, auto_connect=False)
        pipeline = FlinkStreamingPipeline(config=config, neo4j_sink=neo4j_sink, dlq_sink=dlq_sink)
        pipeline.close()
        print("[SUCCESS] Pipeline modules initialized successfully.")
        return

    pipeline = FlinkStreamingPipeline(config=config)

    def handle_sigint(sig, frame):
        logger.info("Termination signal received. Shutting down...")
        pipeline.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    pipeline.run_consumer_loop(max_messages=args.max_messages)


if __name__ == "__main__":
    main()
