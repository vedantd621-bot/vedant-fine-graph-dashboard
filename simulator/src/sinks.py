"""
FinGraph Output Sink Abstraction.
Decouples synthetic event generation from downstream storage/transport mechanisms (stdout, file, Kafka).
"""
import abc
import sys
from pathlib import Path
from typing import Optional

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from simulator.src.config import KafkaConfig, get_kafka_config
    from simulator.src.kafka_producer import KafkaTransactionProducer
    from simulator.src.models import TransactionEvent
except ImportError:
    from config import KafkaConfig, get_kafka_config
    from kafka_producer import KafkaTransactionProducer
    from models import TransactionEvent


class BaseOutputSink(abc.ABC):
    """Abstract base class for transaction event sinks."""

    @abc.abstractmethod
    def write(self, event: TransactionEvent) -> None:
        """Write a single transaction event to the sink."""
        pass

    def flush(self) -> None:
        """Flush buffered writes."""
        pass

    def close(self) -> None:
        """Cleanly close resources."""
        pass

    def __enter__(self) -> "BaseOutputSink":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class StdoutSink(BaseOutputSink):
    """Prints formatted transaction events to standard output."""

    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def write(self, event: TransactionEvent) -> None:
        if not self.quiet:
            print(
                f"[{event.timestamp.strftime('%H:%M:%S')}] {event.transaction_id} | "
                f"{event.from_account} -> {event.to_account} | "
                f"${event.amount:>9.2f} {event.currency.value} | "
                f"{event.transaction_type.value:<12} | {event.scenario_id}"
            )


class FileSink(BaseOutputSink):
    """Writes JSON-Lines serialized transaction events to a file on disk."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = open(self.filepath, "a", encoding="utf-8")

    def write(self, event: TransactionEvent) -> None:
        self.file_handle.write(event.model_dump_json() + "\n")
        self.file_handle.flush()

    def flush(self) -> None:
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.flush()

    def close(self) -> None:
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.flush()
            self.file_handle.close()


class KafkaSink(BaseOutputSink):
    """Publishes transaction events to Apache Kafka topic."""

    def __init__(
        self,
        config: Optional[KafkaConfig] = None,
        bootstrap_servers: Optional[str] = None,
        topic: Optional[str] = None,
        producer: Optional[KafkaTransactionProducer] = None,
        quiet: bool = False,
    ):
        self.quiet = quiet
        self.producer = producer or KafkaTransactionProducer(
            config=config,
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            auto_connect=True,
        )

    def write(self, event: TransactionEvent) -> None:
        meta = self.producer.publish(event)
        if not self.quiet:
            print(
                f"[Kafka: {meta['topic']}:{meta['partition']} @ {meta['offset']}] "
                f"{event.transaction_id} | {event.from_account} -> {event.to_account} | "
                f"${event.amount:>9.2f} {event.currency.value} | {event.scenario_id}"
            )

    def flush(self) -> None:
        if self.producer:
            self.producer.flush()

    def close(self) -> None:
        if self.producer:
            self.producer.close()


def create_output_sink(
    output_spec: str,
    quiet: bool = False,
    kafka_config: Optional[KafkaConfig] = None,
) -> BaseOutputSink:
    """
    Factory creating the appropriate OutputSink based on output_spec:
      - 'stdout': StdoutSink
      - 'file:<path>': FileSink
      - 'kafka': KafkaSink
    """
    spec = output_spec.strip()
    if spec == "stdout":
        return StdoutSink(quiet=quiet)
    elif spec.startswith("file:"):
        path = spec.split("file:", 1)[1]
        return FileSink(filepath=path)
    elif spec == "kafka":
        return KafkaSink(config=kafka_config, quiet=quiet)
    else:
        raise ValueError(
            f"Unsupported output sink specification: '{output_spec}'. Use 'stdout', 'file:<path>', or 'kafka'."
        )
