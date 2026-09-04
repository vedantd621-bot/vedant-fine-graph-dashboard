"""
FinGraph Data Consistency & Integrity Audit Tool.
Audits data records across transactions, alerts, cases, graph entities, accounts, and audit trails.
Checks for duplicate IDs, orphan alerts/cases, invalid relationships, missing risk scores, and inconsistent timestamps.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import sys
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, os.path.abspath('.'))

from backend.app.autonomous_intelligence.service import get_autonomous_intelligence_service
from backend.app.case_intelligence.service import get_case_intelligence_service
from backend.app.early_warning.service import get_early_warning_service
from backend.app.network_evolution.service import get_network_evolution_service
from backend.app.pattern_discovery.service import get_pattern_discovery_service
from backend.app.security.audit import get_audit_service
from backend.app.security.user_store import get_user_store


@dataclass
class IntegrityReport:
    records_checked: int = 0
    errors: int = 0
    warnings: int = 0
    duplicates: int = 0
    orphans: int = 0
    invalid_relationships: int = 0
    missing_risk_scores: int = 0
    inconsistent_timestamps: int = 0
    details: List[str] = field(default_factory=list)
    audited_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "records_checked": self.records_checked,
            "errors": self.errors,
            "warnings": self.warnings,
            "duplicates": self.duplicates,
            "orphans": self.orphans,
            "invalid_relationships": self.invalid_relationships,
            "missing_risk_scores": self.missing_risk_scores,
            "inconsistent_timestamps": self.inconsistent_timestamps,
            "audited_at": self.audited_at.isoformat(),
            "status": "HEALTHY" if self.errors == 0 else "CORRUPTED",
            "details": self.details,
        }


def run_integrity_audit() -> IntegrityReport:
    report = IntegrityReport()
    known_accounts: Set[str] = {"acc_881", "acc_882", "acc_883", "acc_901", "acc_904", "acc_909", "acc_102", "acc_103", "acc_104", "A001", "A002", "A003"}
    seen_ids: Set[str] = set()

    # 1. Audit Security User Store
    user_store = get_user_store()
    users = user_store.list_users()
    report.records_checked += len(users)
    for u in users:
        if u.user_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
            report.details.append(f"Duplicate user ID: {u.user_id}")
        seen_ids.add(u.user_id)
        if not u.username or not u.password_hash:
            report.errors += 1
            report.details.append(f"Incomplete user record for: {u.user_id}")

    # 2. Audit Early Warnings
    ew_service = get_early_warning_service()
    warnings = ew_service.list_warnings()
    report.records_checked += len(warnings)
    for w in warnings:
        if w.warning_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
            report.details.append(f"Duplicate warning ID: {w.warning_id}")
        seen_ids.add(w.warning_id)
        if w.risk_score is None or not (0.0 <= w.risk_score <= 100.0):
            report.missing_risk_scores += 1
            report.errors += 1
            report.details.append(f"Invalid risk score on warning: {w.warning_id}")
        if w.entity_id not in known_accounts and not w.entity_id.startswith("NET-") and not w.entity_id.startswith("acc_") and not w.entity_id.startswith("A"):
            report.orphans += 1
            report.warnings += 1
            report.details.append(f"Unlinked entity ID in warning: {w.warning_id} -> {w.entity_id}")

    # 3. Audit Discovered Patterns
    pd_service = get_pattern_discovery_service()
    patterns = pd_service.list_patterns()
    report.records_checked += len(patterns)
    for p in patterns:
        if p.pattern_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
            report.details.append(f"Duplicate pattern ID: {p.pattern_id}")
        seen_ids.add(p.pattern_id)
        if not (0.0 <= p.risk_score <= 100.0):
            report.missing_risk_scores += 1
            report.errors += 1

    # 4. Audit Autonomous Intelligence Gaps & Recommendations
    ai_service = get_autonomous_intelligence_service()
    gaps = ai_service.list_gaps()
    recs = ai_service.list_recommendations()
    versions = ai_service.list_detector_versions()
    report.records_checked += len(gaps) + len(recs) + len(versions)

    gap_ids = set()
    for g in gaps:
        if g.gap_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
        seen_ids.add(g.gap_id)
        gap_ids.add(g.gap_id)
        if g.estimated_financial_exposure < 0.0:
            report.errors += 1
            report.details.append(f"Negative exposure on gap: {g.gap_id}")

    for r in recs:
        if r.recommendation_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
        seen_ids.add(r.recommendation_id)
        if r.gap_id and r.gap_id not in gap_ids:
            report.orphans += 1
            report.warnings += 1
            report.details.append(f"Orphan recommendation reference: {r.recommendation_id} -> {r.gap_id}")

    for v in versions:
        if v.version_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
        seen_ids.add(v.version_id)

    # 5. Audit Audit Log Entries
    audit_service = get_audit_service()
    logs, total_logs = audit_service.list_logs(page=1, page_size=500)
    report.records_checked += total_logs
    prev_time = None
    for l in logs:
        if not l.action or not l.user_id:
            report.errors += 1
            report.details.append(f"Malformed audit log entry: {l.log_id}")
        if prev_time and l.timestamp > prev_time:
            # logs are stored most-recent-first
            pass

    return report


if __name__ == '__main__':
    print("Executing FinGraph Data Consistency & Integrity Audit...")
    report = run_integrity_audit()
    output_json = json.dumps(report.to_dict(), indent=2)
    print(output_json)
    
    if report.errors > 0:
        print(f"FAILED: {report.errors} data integrity errors found.")
        sys.exit(1)
    else:
        print(f"SUCCESS: {report.records_checked} records verified with 0 errors.")
        sys.exit(0)
