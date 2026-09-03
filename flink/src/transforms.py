"""
FinGraph Flink Streaming Transformations & Validation Logic.
Decodes raw Kafka bytes, applies rigorous schema validation, normalizes timestamps to UTC,
and routes malformed messages to DLQ payloads.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from flink.src.schemas import (
    CanonicalTransaction,
    DLQEvent,
    ValidationResult,
    VALID_CURRENCIES,
    DEFAULT_SCENARIO,
)

logger = logging.getLogger("FinGraph.FlinkTransforms")


def parse_iso_timestamp(ts_val: Any) -> datetime:
    """Parses an ISO 8601 string or epoch into a timezone-aware UTC datetime."""
    if isinstance(ts_val, datetime):
        if ts_val.tzinfo is None:
            return ts_val.replace(tzinfo=timezone.utc)
        return ts_val.astimezone(timezone.utc)

    if isinstance(ts_val, (int, float)):
        # Epoch seconds or milliseconds
        if ts_val > 1e11:
            ts_val = ts_val / 1000.0
        return datetime.fromtimestamp(ts_val, tz=timezone.utc)

    if isinstance(ts_val, str):
        clean_str = ts_val.strip()
        if clean_str.endswith("Z"):
            clean_str = clean_str[:-1] + "+00:00"
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    raise ValueError(f"Unsupported timestamp format: {ts_val}")


def decode_and_validate(
    raw_input: Union[bytes, str, Dict[str, Any]],
    topic: str = "transactions",
    partition: int = 0,
    offset: int = 0,
) -> ValidationResult:
    """
    Decodes, parses, and validates raw Kafka stream records.
    Never raises unhandled exceptions; cleanly returns ValidationResult with DLQEvent on error.
    """
    now_utc = datetime.now(timezone.utc).isoformat()

    # 1. UTF-8 Decoding
    if isinstance(raw_input, bytes):
        try:
            raw_str = raw_input.decode("utf-8")
        except UnicodeDecodeError as exc:
            return ValidationResult(
                is_valid=False,
                dlq_event=DLQEvent(
                    raw_payload=str(raw_input),
                    error_reason=f"UTF-8 decode failed: {exc}",
                    timestamp=now_utc,
                    source_topic=topic,
                    partition=partition,
                    offset=offset,
                ),
            )
    elif isinstance(raw_input, str):
        raw_str = raw_input
    elif isinstance(raw_input, dict):
        raw_str = json.dumps(raw_input)
    else:
        return ValidationResult(
            is_valid=False,
            dlq_event=DLQEvent(
                raw_payload=str(raw_input),
                error_reason=f"Unexpected input type: {type(raw_input).__name__}",
                timestamp=now_utc,
                source_topic=topic,
                partition=partition,
                offset=offset,
            ),
        )

    # 2. JSON Deserialization
    try:
        data = json.loads(raw_str)
        if not isinstance(data, dict):
            raise ValueError(f"JSON payload must be an object, got {type(data).__name__}")
    except Exception as exc:
        return ValidationResult(
            is_valid=False,
            dlq_event=DLQEvent(
                raw_payload=raw_str,
                error_reason=f"JSON parsing error: {exc}",
                timestamp=now_utc,
                source_topic=topic,
                partition=partition,
                offset=offset,
            ),
        )

    # 3. Field Validations
    tx_id = str(data.get("transaction_id", "")).strip()
    if not tx_id:
        return ValidationResult(
            is_valid=False,
            dlq_event=DLQEvent(
                raw_payload=raw_str,
                error_reason="Missing or empty 'transaction_id'",
                timestamp=now_utc,
                source_topic=topic,
                partition=partition,
                offset=offset,
            ),
        )

    from_acc = str(data.get("from_account", "")).strip()
    to_acc = str(data.get("to_account", "")).strip()
    if not from_acc:
        return ValidationResult(
            is_valid=False,
            dlq_event=DLQEvent(
                raw_payload=raw_str,
                error_reason="Missing or empty 'from_account'",
                timestamp=now_utc,
                source_topic=topic,
                partition=partition,
                offset=offset,
            ),
        )
    if not to_acc:
        return ValidationResult(
            is_valid=False,
            dlq_event=DLQEvent(
                raw_payload=raw_str,
                error_reason="Missing or empty 'to_account'",
                timestamp=now_utc,
                source_topic=topic,
                partition=partition,
                offset=offset,
            ),
        )

    raw_amount = data.get("amount")
    try:
        amount = float(raw_amount)
        if amount <= 0.0:
            return ValidationResult(
                is_valid=False,
                dlq_event=DLQEvent(
                    raw_payload=raw_str,
                    error_reason=f"Amount must be strictly positive, got: {amount}",
                    timestamp=now_utc,
                    source_topic=topic,
                    partition=partition,
                    offset=offset,
                ),
            )
    except (TypeError, ValueError):
        return ValidationResult(
            is_valid=False,
            dlq_event=DLQEvent(
                raw_payload=raw_str,
                error_reason=f"Amount must be numeric, got: {raw_amount}",
                timestamp=now_utc,
                source_topic=topic,
                partition=partition,
                offset=offset,
            ),
        )

    currency = str(data.get("currency", "USD")).strip().upper()
    if currency not in VALID_CURRENCIES:
        return ValidationResult(
            is_valid=False,
            dlq_event=DLQEvent(
                raw_payload=raw_str,
                error_reason=f"Unsupported currency: '{currency}' (Allowed: {sorted(list(VALID_CURRENCIES))})",
                timestamp=now_utc,
                source_topic=topic,
                partition=partition,
                offset=offset,
            ),
        )

    raw_ts = data.get("timestamp")
    try:
        dt = parse_iso_timestamp(raw_ts)
    except Exception as exc:
        return ValidationResult(
            is_valid=False,
            dlq_event=DLQEvent(
                raw_payload=raw_str,
                error_reason=f"Invalid timestamp format: {raw_ts} ({exc})",
                timestamp=now_utc,
                source_topic=topic,
                partition=partition,
                offset=offset,
            ),
        )

    # 4. Canonical Model Construction
    scenario_id = str(data.get("scenario_id", DEFAULT_SCENARIO)).strip() or DEFAULT_SCENARIO
    tx_type = str(data.get("transaction_type", "transfer")).strip().lower()
    channel = str(data.get("channel", "online")).strip().lower()

    canonical = CanonicalTransaction(
        transaction_id=tx_id,
        from_account=from_acc,
        to_account=to_acc,
        amount=amount,
        currency=currency,
        timestamp=dt,
        scenario_id=scenario_id,
        transaction_type=tx_type,
        channel=channel,
        from_person_id=str(data.get("from_person_id", "")).strip() or None,
        to_person_id=str(data.get("to_person_id", "")).strip() or None,
        from_bank_id=str(data.get("from_bank_id", "")).strip() or None,
        to_bank_id=str(data.get("to_bank_id", "")).strip() or None,
        from_account_type=str(data.get("from_account_type", "checking")).strip().lower(),
        to_account_type=str(data.get("to_account_type", "checking")).strip().lower(),
    )

    return ValidationResult(is_valid=True, transaction=canonical, dlq_event=None)


def extract_event_timestamp(tx: CanonicalTransaction) -> int:
    """Extracts epoch milliseconds from a canonical transaction for Flink watermarking."""
    return int(tx.timestamp.timestamp() * 1000)
