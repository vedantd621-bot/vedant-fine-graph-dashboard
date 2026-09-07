"""
Secure Exporter Engine with CSV Formula Injection Protection.
"""
import csv
import hashlib
import io
import json
from typing import Any, Dict, List, Tuple

# Characters that trigger spreadsheet formula evaluation (CWE-1236)
_FORMULA_TRIGGERS = ('=', '+', '-', '@', '\t', '\r')


def sanitize_csv_cell(value: Any) -> str:
    """Neutralize spreadsheet formula injection by prefixing with a single quote."""
    s = str(value) if value is not None else ""
    if s and s[0] in _FORMULA_TRIGGERS:
        return "'" + s
    return s


def export_to_json(data: Any) -> Tuple[str, str]:
    """Serializes data to formatted JSON and computes SHA-256 hash."""
    if hasattr(data, "model_dump"):
        raw = data.model_dump(mode="json")
    elif isinstance(data, list):
        raw = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in data]
    else:
        raw = data
    content = json.dumps(raw, indent=2, default=str)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return content, content_hash


def export_to_csv(rows: List[Dict[str, Any]], max_rows: int = 10000) -> Tuple[str, str, int]:
    """Serializes rows to CSV with formula injection neutralization and row bounding."""
    if not rows:
        return "", hashlib.sha256(b"").hexdigest(), 0

    bounded_rows = rows[:max_rows]
    output = io.StringIO()
    fieldnames = list(bounded_rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    for row in bounded_rows:
        sanitized = {k: sanitize_csv_cell(v) for k, v in row.items()}
        writer.writerow(sanitized)

    content = output.getvalue()
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return content, content_hash, len(bounded_rows)


def report_to_csv_rows(report_data: Any, report_type: str) -> List[Dict[str, Any]]:
    """Flattens report payload into tabular rows for CSV generation."""
    if isinstance(report_data, list):
        return [dict(r) if isinstance(r, dict) else {"item": str(r)} for r in report_data]
    elif isinstance(report_data, dict):
        flattened = {}
        for k, v in report_data.items():
            if isinstance(v, (list, dict)):
                flattened[k] = json.dumps(v)
            else:
                flattened[k] = v
        return [flattened]
    elif hasattr(report_data, "model_dump"):
        d = report_data.model_dump(mode="json")
        return [d]
    return [{"report_type": report_type, "payload": str(report_data)}]
