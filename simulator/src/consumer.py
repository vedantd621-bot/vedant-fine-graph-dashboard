#!/usr/bin/env python3
"""
FinGraph Kafka Debug Consumer.
Subscribes to the Kafka 'transactions' topic, deserializes JSON messages,
validates payloads against the TransactionEvent Pydantic schema, and logs real-time stream activity.
"""
import argparse
import json
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
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError, NoBrokersAvailable
except ImportError:
    KafkaConsumer = None
    KafkaError = Exception
    NoBrokersAvailable = Exception

try:
    from simulator.src.config import KafkaConfig, get_kafka_config
    from simulator.src.models import TransactionEvent
except ImportError:
    from config import KafkaConfig, get_kafka_config
    from models import TransactionEvent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [KafkaConsumer] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FinGraph.KafkaConsumer")


def parse_args() -> argparse.Namespace:
    config = get_kafka_config()
    parser = argparse.ArgumentParser(
        description="FinGraph Kafka Debug Consumer CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--bootstrap-servers",
        type=str,
        default=config.bootstrap_servers,
        help="Kafka bootstrap server host:port",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=config.topic,
        help="Kafka topic to consume from",
    )
    parser.add_argument(
        "--group-id",
        type=str,
        default="fingraph-debug-consumer",
        help="Kafka consumer group ID",
    )
    parser.add_argument(
        "--from-beginning",
        action="store_true",
        help="Read topic from earliest available offset",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="Consumer timeout in seconds (0 = wait indefinitely)",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=0,
        help="Stop after consuming N messages (0 = unlimited)",
    )
    return parser.parse_args()


class KafkaTransactionConsumer:
    """Consumes and validates TransactionEvents from Kafka."""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str = "fingraph-debug-consumer",
        auto_offset_reset: str = "latest",
    ):
        if KafkaConsumer is None:
            raise ImportError(
                "kafka-python or kafka-python-ng is required. Install via requirements.txt"
            )

        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset

        server_list = [s.strip() for s in bootstrap_servers.split(",") if s.strip()]

        logger.info(
            f"Initializing Kafka consumer (servers={server_list}, topic={topic}, group={group_id}, offset={auto_offset_reset})..."
        )
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=server_list,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=lambda m: m.decode("utf-8"),
            consumer_timeout_ms=1000,  # 1s polling interval
        )
        logger.info(f"Consumer successfully subscribed to topic: '{topic}'")

    def consume_loop(
        self, timeout_sec: int = 0, max_messages: int = 0
    ) -> dict:
        """
        Runs consumer loop until timeout or max messages reached.
        Safely validates each payload with TransactionEvent schema.
        """
        valid_count = 0
        malformed_count = 0
        total_amount = 0.0
        scenario_counts = {}

        start_time = time.time()
        print("\n" + "=" * 70)
        print(f"  FinGraph Live Kafka Consumer | Topic: {self.topic}")
        print("  Waiting for incoming transaction stream... (Ctrl+C to stop)")
        print("=" * 70 + "\n")

        try:
            while True:
                now = time.time()
                if timeout_sec > 0 and (now - start_time) >= timeout_sec:
                    break
                if max_messages > 0 and valid_count >= max_messages:
                    break

                for message in self.consumer:
                    raw_val = message.value
                    try:
                        # 1. Decode & Validate Pydantic Schema
                        event = TransactionEvent.model_validate_json(raw_val)
                        valid_count += 1
                        total_amount += event.amount
                        scenario_counts[event.scenario_id] = (
                            scenario_counts.get(event.scenario_id, 0) + 1
                        )

                        # 2. Render structured output
                        print(
                            f"[Kafka P{message.partition}:O{message.offset}] "
                            f"{event.transaction_id:<10} | "
                            f"{event.from_account} -> {event.to_account} | "
                            f"${event.amount:>9.2f} {event.currency.value} | "
                            f"{event.transaction_type.value:<12} | "
                            f"{event.scenario_id}"
                        )

                    except Exception as val_err:
                        malformed_count += 1
                        logger.warning(
                            f"Rejected malformed record at P{message.partition}:O{message.offset}: {val_err}"
                        )
                        # Continue processing without crashing

                    if max_messages > 0 and valid_count >= max_messages:
                        break

        except KeyboardInterrupt:
            print("\n[*] Consumer interrupted by user.")
        finally:
            self.consumer.close()

        elapsed = max(0.001, time.time() - start_time)
        print("\n" + "=" * 70)
        print("  Kafka Consumer Session Summary")
        print("=" * 70)
        print(f"  Valid Messages Consumed:     {valid_count}")
        print(f"  Malformed Messages Skipped:  {malformed_count}")
        print(f"  Total Monetary Volume:       ${total_amount:,.2f} USD")
        print(f"  Session Elapsed Time:        {elapsed:.2f}s")
        print("  Scenario Distribution:")
        for sc, count in sorted(scenario_counts.items(), key=lambda x: -x[1]):
            print(f"    - {sc:<25} : {count:>4} events")
        print("=" * 70)

        return {
            "valid_count": valid_count,
            "malformed_count": malformed_count,
            "total_amount": total_amount,
            "scenarios": scenario_counts,
        }


def main():
    args = parse_args()
    offset_mode = "earliest" if args.from_beginning else "latest"

    consumer = KafkaTransactionConsumer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        group_id=args.group_id,
        auto_offset_reset=offset_mode,
    )

    consumer.consume_loop(
        timeout_sec=args.timeout,
        max_messages=args.max_messages,
    )


if __name__ == "__main__":
    main()
