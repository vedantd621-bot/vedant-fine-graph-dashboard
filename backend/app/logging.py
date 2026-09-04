"""
FinGraph Structured JSON Logging Formatter.
Ensures uniform machine-parsable logging across all runtime microservices without leaking sensitive credentials.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Include request_id if available
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(level: str = "INFO", json_format: bool = False):
    """Configures root logger with appropriate formatter and log level."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    if json_format:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s", datefmt="%H:%M:%S")
        )
    root_logger.addHandler(handler)
