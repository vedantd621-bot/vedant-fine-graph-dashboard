"""
FinGraph Streaming Observability & Pipeline Metrics.
Tracks processing rates, error counts, DLQ dispatches, and end-to-end latency timers.
"""
import threading
import time
from typing import Any, Dict


class StreamingMetrics:
    """Thread-safe real-time metric counter for the Flink streaming pipeline."""

    def __init__(self):
        self._lock = threading.Lock()
        self.events_received = 0
        self.events_valid = 0
        self.events_invalid = 0
        self.events_written = 0
        self.events_failed = 0
        self.dlq_events = 0
        self.duplicate_events = 0
        self.start_time = time.monotonic()

    def record_received(self) -> None:
        with self._lock:
            self.events_received += 1

    def record_valid(self) -> None:
        with self._lock:
            self.events_valid += 1

    def record_invalid(self) -> None:
        with self._lock:
            self.events_invalid += 1
            self.dlq_events += 1

    def record_written(self, count: int = 1) -> None:
        with self._lock:
            self.events_written += count

    def record_failed(self, count: int = 1) -> None:
        with self._lock:
            self.events_failed += count

    def record_duplicate(self) -> None:
        with self._lock:
            self.duplicate_events += 1

    def snapshot(self) -> Dict[str, Any]:
        """Returns a point-in-time dictionary of metrics."""
        with self._lock:
            elapsed = max(0.001, time.monotonic() - self.start_time)
            throughput = self.events_written / elapsed
            return {
                "events_received": self.events_received,
                "events_valid": self.events_valid,
                "events_invalid": self.events_invalid,
                "events_written": self.events_written,
                "events_failed": self.events_failed,
                "dlq_events": self.dlq_events,
                "duplicate_events": self.duplicate_events,
                "elapsed_seconds": round(elapsed, 2),
                "events_per_second": round(throughput, 2),
            }

    def reset(self) -> None:
        with self._lock:
            self.events_received = 0
            self.events_valid = 0
            self.events_invalid = 0
            self.events_written = 0
            self.events_failed = 0
            self.dlq_events = 0
            self.duplicate_events = 0
            self.start_time = time.monotonic()
