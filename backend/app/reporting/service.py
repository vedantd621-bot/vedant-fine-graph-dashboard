"""
Enterprise Reporting Service.
"""
from datetime import datetime, timedelta, timezone
import random
import threading
from typing import Dict, List, Optional

from backend.app.reporting.exporter import export_to_csv, export_to_json, report_to_csv_rows
from backend.app.reporting.models import (
    CreateReportRequest, CreateScheduleRequest, ReportFormat, ReportSchedule,
    ReportSnapshot, ReportStatus, ReportType, ScheduleFrequency
)


class ReportingService:
    """Thread-safe report snapshot repository and scheduling manager."""

    def __init__(self):
        self._snapshots: Dict[str, ReportSnapshot] = {}
        self._schedules: Dict[str, ReportSchedule] = {}
        self._lock = threading.RLock()
        self._seed_sample_reports()

    def _seed_sample_reports(self):
        sample_types = [
            ReportType.EXECUTIVE_FRAUD_REPORT,
            ReportType.FRAUD_NETWORK_REPORT,
            ReportType.OPERATIONS_REPORT,
            ReportType.RISK_REPORT,
        ]
        for rtype in sample_types:
            data = self._compile_report_data(rtype, "tnt_default")
            content, chash = export_to_json(data)
            snap = ReportSnapshot(
                report_type=rtype,
                tenant_id="tnt_default",
                title=f"Sample {rtype.value.replace('_', ' ').title()}",
                format=ReportFormat.JSON,
                status=ReportStatus.COMPLETED,
                created_by="system",
                content_hash=chash,
                row_count=1,
                content=data,
            )
            self._snapshots[snap.report_id] = snap

    def _compile_report_data(self, report_type: ReportType, tenant_id: str, filters=None) -> dict:
        seed = hash(f"{tenant_id}:{report_type.value}") % (2**31)
        rng = random.Random(seed)
        now = datetime.now(timezone.utc)

        if report_type == ReportType.EXECUTIVE_FRAUD_REPORT:
            return {
                "period": "Last 30 Days",
                "tenant_id": tenant_id,
                "total_alerts": rng.randint(120, 350),
                "confirmed_fraud_cases": rng.randint(20, 45),
                "prevented_loss_usd": round(rng.uniform(500000.0, 1500000.0), 2),
                "fraud_rate_pct": round(rng.uniform(1.8, 3.2), 2),
                "top_syndicates": ["LoopRing_North", "Smurf_Alpha"],
                "generated_at": now.isoformat(),
            }
        elif report_type == ReportType.FRAUD_NETWORK_REPORT:
            return {
                "period": "Last 30 Days",
                "tenant_id": tenant_id,
                "active_networks": rng.randint(8, 20),
                "emerging_clusters": rng.randint(2, 6),
                "total_network_exposure": round(rng.uniform(300000.0, 850000.0), 2),
                "top_originators": ["ACC_991", "ACC_442"],
                "generated_at": now.isoformat(),
            }
        elif report_type == ReportType.CAMPAIGN_REPORT:
            return {
                "period": "Last 30 Days",
                "tenant_id": tenant_id,
                "active_campaigns": rng.randint(3, 8),
                "campaign_risk_avg": round(rng.uniform(55.0, 85.0), 1),
                "linked_cases": rng.randint(12, 35),
                "generated_at": now.isoformat(),
            }
        elif report_type == ReportType.INVESTIGATION_REPORT:
            return {
                "period": "Last 30 Days",
                "tenant_id": tenant_id,
                "open_cases": rng.randint(15, 40),
                "closed_cases": rng.randint(30, 80),
                "median_resolution_hours": round(rng.uniform(4.0, 18.0), 1),
                "sla_adherence_pct": round(rng.uniform(92.0, 99.0), 1),
                "generated_at": now.isoformat(),
            }
        elif report_type == ReportType.DETECTOR_PERFORMANCE_REPORT:
            return {
                "period": "Last 30 Days",
                "tenant_id": tenant_id,
                "detectors_evaluated": 7,
                "overall_precision": round(rng.uniform(0.72, 0.94), 3),
                "false_positive_rate": round(rng.uniform(0.04, 0.12), 3),
                "top_detector": "CircularFlowDetector",
                "generated_at": now.isoformat(),
            }
        elif report_type == ReportType.OPERATIONS_REPORT:
            return {
                "period": "Last 30 Days",
                "tenant_id": tenant_id,
                "total_triage_actions": rng.randint(150, 450),
                "investigator_capacity_pct": round(rng.uniform(65.0, 88.0), 1),
                "breached_slas": rng.randint(0, 4),
                "generated_at": now.isoformat(),
            }
        elif report_type == ReportType.RISK_REPORT:
            return {
                "period": "Last 30 Days",
                "tenant_id": tenant_id,
                "mean_account_risk": round(rng.uniform(32.0, 58.0), 1),
                "critical_risk_accounts": rng.randint(5, 22),
                "risk_distribution": {"CRITICAL": 8, "HIGH": 24, "MEDIUM": 85, "LOW": 210},
                "generated_at": now.isoformat(),
            }
        else:  # TENANT_POSTURE_REPORT
            return {
                "period": "Last 30 Days",
                "tenant_id": tenant_id,
                "posture_score": round(rng.uniform(35.0, 65.0), 1),
                "threat_level": "MODERATE",
                "compliance_status": "AUDITED_COMPLIANT",
                "generated_at": now.isoformat(),
            }

    def generate_report(self, req: CreateReportRequest, tenant_id: str, created_by: str) -> ReportSnapshot:
        data = self._compile_report_data(req.report_type, tenant_id, req.filters)
        title = req.title or f"{req.report_type.value.replace('_', ' ').title()} - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

        if req.format == ReportFormat.CSV:
            rows = report_to_csv_rows(data, req.report_type.value)
            content, chash, row_count = export_to_csv(rows)
        else:
            content, chash = export_to_json(data)
            row_count = 1

        snap = ReportSnapshot(
            report_type=req.report_type,
            tenant_id=tenant_id,
            title=title,
            format=req.format,
            status=ReportStatus.COMPLETED,
            created_by=created_by,
            parameters={"filters": req.filters.model_dump() if req.filters else {}},
            content_hash=chash,
            row_count=row_count,
            content=data,
        )
        with self._lock:
            self._snapshots[snap.report_id] = snap
        return snap

    def get_snapshot(self, report_id: str, tenant_id: str) -> Optional[ReportSnapshot]:
        with self._lock:
            s = self._snapshots.get(report_id)
            if not s:
                return None
            if tenant_id != "GLOBAL" and s.tenant_id != tenant_id:
                return None
            return s

    def list_snapshots(self, tenant_id: str, limit: int = 50) -> List[ReportSnapshot]:
        with self._lock:
            if tenant_id == "GLOBAL":
                snaps = list(self._snapshots.values())
            else:
                snaps = [s for s in self._snapshots.values() if s.tenant_id == tenant_id]
        snaps.sort(key=lambda x: x.created_at, reverse=True)
        return snaps[:limit]

    def create_schedule(self, req: CreateScheduleRequest, tenant_id: str, created_by: str) -> ReportSchedule:
        now = datetime.now(timezone.utc)
        if req.frequency == ScheduleFrequency.DAILY:
            next_run = now + timedelta(days=1)
        elif req.frequency == ScheduleFrequency.WEEKLY:
            next_run = now + timedelta(weeks=1)
        else:
            next_run = now + timedelta(days=30)

        title = req.title or f"Scheduled {req.report_type.value.replace('_', ' ').title()}"
        schedule = ReportSchedule(
            report_type=req.report_type,
            tenant_id=tenant_id,
            frequency=req.frequency,
            title=title,
            format=req.format,
            created_by=created_by,
            next_run_at=next_run,
            filters=req.filters,
        )
        with self._lock:
            self._schedules[schedule.schedule_id] = schedule
        return schedule

    def list_schedules(self, tenant_id: str) -> List[ReportSchedule]:
        with self._lock:
            if tenant_id == "GLOBAL":
                return list(self._schedules.values())
            return [s for s in self._schedules.values() if s.tenant_id == tenant_id]

    def export_snapshot(self, report_id: str, tenant_id: str, fmt: ReportFormat):
        snap = self.get_snapshot(report_id, tenant_id)
        if not snap:
            raise ValueError(f"Report '{report_id}' not found.")

        if fmt == ReportFormat.CSV:
            rows = report_to_csv_rows(snap.content, snap.report_type.value)
            content, chash, row_count = export_to_csv(rows)
            return content, chash, "text/csv", f"{snap.report_type.value.lower()}.csv"
        else:
            content, chash = export_to_json(snap.content)
            return content, chash, "application/json", f"{snap.report_type.value.lower()}.json"


_reporting_service: Optional[ReportingService] = None


def get_reporting_service() -> ReportingService:
    global _reporting_service
    if _reporting_service is None:
        _reporting_service = ReportingService()
    return _reporting_service
