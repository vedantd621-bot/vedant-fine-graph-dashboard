"""
FinGraph Flink Canonical Schemas and Validation Result Models.
Ensures stream records are strictly validated and normalized before graph persistence.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json


VALID_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD", "CHF", "JPY", "SGD"}
DEFAULT_SCENARIO = "SC_NORMAL"


@dataclass(frozen=True)
class CanonicalTransaction:
    """Canonical internal normalized transaction record."""
    transaction_id: str
    from_account: str
    to_account: str
    amount: float
    currency: str
    timestamp: datetime
    scenario_id: str
    transaction_type: str = "transfer"
    channel: str = "online"
    from_person_id: Optional[str] = None
    to_person_id: Optional[str] = None
    from_bank_id: Optional[str] = None
    to_bank_id: Optional[str] = None
    from_account_type: Optional[str] = "checking"
    to_account_type: Optional[str] = "checking"

    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Converts canonical transaction to a dictionary suitable for Neo4j Cypher parameters."""
        return {
            "transaction_id": self.transaction_id,
            "from_account": self.from_account,
            "to_account": self.to_account,
            "amount": float(self.amount),
            "currency": self.currency,
            "timestamp": self.timestamp.isoformat(),
            "scenario_id": self.scenario_id,
            "transaction_type": self.transaction_type,
            "channel": self.channel,
            "from_person_id": self.from_person_id or "",
            "to_person_id": self.to_person_id or "",
            "from_bank_id": self.from_bank_id or "",
            "to_bank_id": self.to_bank_id or "",
            "from_account_type": self.from_account_type or "checking",
            "to_account_type": self.to_account_type or "checking",
        }


@dataclass(frozen=True)
class DLQEvent:
    """Dead-Letter Queue event containing diagnostic failure metadata."""
    raw_payload: str
    error_reason: str
    timestamp: str
    source_topic: str = "transactions"
    partition: int = 0
    offset: int = 0

    def to_json(self) -> str:
        """Serializes DLQ event to UTF-8 JSON string."""
        return json.dumps({
            "raw_payload": self.raw_payload,
            "error_reason": self.error_reason,
            "timestamp": self.timestamp,
            "source_topic": self.source_topic,
            "partition": self.partition,
            "offset": self.offset,
        })


@dataclass(frozen=True)
class ValidationResult:
    """Represents the outcome of transaction decoding and schema validation."""
    is_valid: bool
    transaction: Optional[CanonicalTransaction] = None
    dlq_event: Optional[DLQEvent] = None
