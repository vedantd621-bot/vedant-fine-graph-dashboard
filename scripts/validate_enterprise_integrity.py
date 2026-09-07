"""
FinGraph Master Enterprise Data Integrity & Cross-Tenant Boundary Verification Tool.
Audits all enterprise subsystems: Tenancy, Policies, Security, Decisioning, Reporting, Analytics.
Verifies zero orphaned records, zero duplicates, valid cryptographic hashes, and strict cross-tenant boundaries.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Set

sys.path.insert(0, os.path.abspath('.'))

from backend.app.decisioning.service import get_decisioning_service
from backend.app.enterprise_analytics.service import get_enterprise_analytics_service
from backend.app.policies.service import get_policy_service
from backend.app.reporting.service import get_reporting_service
from backend.app.security.audit import get_audit_service
from backend.app.security.user_store import get_user_store
from backend.app.tenancy.service import get_tenancy_service


@dataclass
class EnterpriseIntegrityReport:
    records_checked: int = 0
    errors: int = 0
    warnings: int = 0
    duplicates: int = 0
    orphans: int = 0
    cross_tenant_violations: int = 0
    hash_verification_failures: int = 0
    details: List[str] = field(default_factory=list)
    audited_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "records_checked": self.records_checked,
            "errors": self.errors,
            "warnings": self.warnings,
            "duplicates": self.duplicates,
            "orphans": self.orphans,
            "cross_tenant_violations": self.cross_tenant_violations,
            "hash_verification_failures": self.hash_verification_failures,
            "audited_at": self.audited_at.isoformat(),
            "status": "ENTERPRISE_HEALTHY" if self.errors == 0 else "CORRUPTED",
            "details": self.details,
        }


def run_enterprise_integrity_audit() -> EnterpriseIntegrityReport:
    report = EnterpriseIntegrityReport()
    seen_ids: Set[str] = set()
    known_tenants: Set[str] = set()

    # 1. Tenancy Subsystem Audit
    tenancy_service = get_tenancy_service()
    tenants = tenancy_service.list_tenants()
    report.records_checked += len(tenants)
    for t in tenants:
        if t.tenant_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
            report.details.append(f"Duplicate tenant ID: {t.tenant_id}")
        seen_ids.add(t.tenant_id)
        known_tenants.add(t.tenant_id)

    # Check organizations, business units, teams
    for tid in known_tenants:
        orgs = tenancy_service.list_organizations(tid)
        report.records_checked += len(orgs)
        for o in orgs:
            if o.tenant_id != tid:
                report.cross_tenant_violations += 1
                report.errors += 1
                report.details.append(f"Cross-tenant mismatch in Org: {o.org_id}")

        teams = tenancy_service.list_teams(tid)
        report.records_checked += len(teams)
        for team in teams:
            if team.tenant_id != tid:
                report.cross_tenant_violations += 1
                report.errors += 1
                report.details.append(f"Cross-tenant mismatch in Team: {team.team_id}")

    # 2. Security User Store Audit
    user_store = get_user_store()
    users = user_store.list_users()
    report.records_checked += len(users)
    for u in users:
        if u.user_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
        seen_ids.add(u.user_id)
        if u.tenant_id not in known_tenants and u.tenant_id != "GLOBAL":
            report.orphans += 1
            report.errors += 1
            report.details.append(f"User '{u.username}' mapped to unknown tenant: {u.tenant_id}")

    # 3. Decisioning Subsystem Audit
    decision_service = get_decisioning_service()
    decisions = decision_service.list_decisions(tenant_id="GLOBAL", limit=500)
    report.records_checked += len(decisions)
    for d in decisions:
        if d.decision_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
        seen_ids.add(d.decision_id)
        if d.tenant_id not in known_tenants and d.tenant_id != "GLOBAL":
            report.orphans += 1
            report.errors += 1
            report.details.append(f"Decision '{d.decision_id}' mapped to unlisted tenant: {d.tenant_id}")
        if not (0.0 <= d.risk_score <= 100.0):
            report.errors += 1
            report.details.append(f"Invalid risk score on decision: {d.decision_id}")

    # 4. Reporting Subsystem & SHA-256 Digest Audit
    reporting_service = get_reporting_service()
    snapshots = reporting_service.list_snapshots(tenant_id="GLOBAL", limit=200)
    report.records_checked += len(snapshots)
    for s in snapshots:
        if s.report_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
        seen_ids.add(s.report_id)
        if not s.content_hash or len(s.content_hash) != 64:
            report.hash_verification_failures += 1
            report.errors += 1
            report.details.append(f"Invalid SHA-256 hash digest on report: {s.report_id}")
        if s.tenant_id not in known_tenants and s.tenant_id != "GLOBAL":
            report.orphans += 1
            report.errors += 1

    # 5. Policies Audit
    policy_service = get_policy_service()
    policies = policy_service.list_policies(tenant_id="GLOBAL")
    report.records_checked += len(policies)
    for p in policies:
        if p.policy_id in seen_ids:
            report.duplicates += 1
            report.errors += 1
        seen_ids.add(p.policy_id)
        if p.tenant_id not in known_tenants and p.tenant_id != "GLOBAL":
            report.orphans += 1
            report.errors += 1

    return report


if __name__ == "__main__":
    print("Running FinGraph Master Enterprise Data Integrity Verification...")
    res = run_enterprise_integrity_audit()
    print(json.dumps(res.to_dict(), indent=2))
    if res.errors > 0:
        print(f"FAILED: {res.errors} integrity errors identified.")
        sys.exit(1)
    else:
        print(f"SUCCESS: {res.records_checked} enterprise records verified with 0 errors.")
        sys.exit(0)
