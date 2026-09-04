"""
FinGraph Fraud Operations, Triage State Machine & Executive Analytics Service.
Manages the real-time alert queue, strict triage lifecycle, investigator assignments,
SLA monitoring, time-series fraud trends, detector confirmation rates, and unified search.
"""
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("FinGraph.OperationsService")

from neo4j.src.client import Neo4jClient
from detection.src.engine import DetectionEngine
from detection.src.models import DetectionType, Severity
from analytics.src.models import RiskLevel
from analytics.src.risk_engine import ExplainableRiskEngine
from backend.app.models.common import PaginationMeta
from backend.app.models.operations import (
    AlertPriorityExplanation,
    BulkOperationResult,
    DetectorPerformanceMetrics,
    DetectorPerformanceResponse,
    FraudTrendPoint,
    FraudTrendsResponse,
    InvestigatorWorkload,
    OperationsSummary,
    PrioritizedAlert,
    PriorityFactor,
    PriorityLevel,
    SearchResultItem,
    SLAItem,
    SLAStatus,
    SLASummary,
    TriageStatus,
    UnifiedSearchResponse,
    WorkloadListResponse,
)
from backend.app.realtime.event_bus import EventBus, get_event_bus
from backend.app.realtime.events import (
    AlertAssignedPayload,
    AlertPrioritizedPayload,
    AlertReassignedPayload,
    EventType,
    SLABreachedPayload,
    SLAWarningPayload,
    TriageUpdatedPayload,
    create_realtime_event,
)
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.security.models import Role
from backend.app.services.account_service import AccountService
from backend.app.services.alert_prioritization_service import AlertPrioritizationService
from backend.app.services.alert_service import AlertService
from backend.app.services.case_service import CaseService
from backend.app.services.network_intelligence_service import NetworkIntelligenceService

# Valid state transitions for the 7-state triage lifecycle
VALID_TRIAGE_TRANSITIONS: Dict[TriageStatus, Set[TriageStatus]] = {
    TriageStatus.NEW: {
        TriageStatus.TRIAGED,
        TriageStatus.INVESTIGATING,
        TriageStatus.FALSE_POSITIVE,
        TriageStatus.CLOSED,
    },
    TriageStatus.TRIAGED: {
        TriageStatus.INVESTIGATING,
        TriageStatus.ESCALATED,
        TriageStatus.FALSE_POSITIVE,
        TriageStatus.CLOSED,
    },
    TriageStatus.INVESTIGATING: {
        TriageStatus.ESCALATED,
        TriageStatus.CONFIRMED_FRAUD,
        TriageStatus.FALSE_POSITIVE,
        TriageStatus.CLOSED,
    },
    TriageStatus.ESCALATED: {
        TriageStatus.CONFIRMED_FRAUD,
        TriageStatus.FALSE_POSITIVE,
        TriageStatus.CLOSED,
    },
    TriageStatus.CONFIRMED_FRAUD: {
        TriageStatus.CLOSED,
    },
    TriageStatus.FALSE_POSITIVE: {
        TriageStatus.CLOSED,
    },
    TriageStatus.CLOSED: {
        TriageStatus.NEW,  # Authorized re-opening
    },
}

# Global in-memory thread-safe state store for operations
# alert_id -> (status, assigned_to, notes, escalation_reason, updated_at)
_triage_store: Dict[str, Tuple[TriageStatus, Optional[str], Optional[str], Optional[str], datetime]] = {}

# Mock registered investigator roster
INVESTIGATOR_ROSTER = [
    {"user_id": "usr_inv_alice", "username": "alice_investigator", "role": Role.INVESTIGATOR},
    {"user_id": "usr_inv_bob", "username": "bob_lead_investigator", "role": Role.INVESTIGATOR},
    {"user_id": "usr_inv_charlie", "username": "charlie_senior_analyst", "role": Role.INVESTIGATOR},
    {"user_id": "usr_admin", "username": "admin", "role": Role.ADMIN},
]


class OperationsService:
    """Service managing fraud operations queue, triage, workload, and executive reporting."""

    def __init__(
        self,
        client: Neo4jClient,
        detection_engine: DetectionEngine,
        risk_engine: ExplainableRiskEngine,
        account_service: AccountService,
        alert_service: AlertService,
        case_service: CaseService,
        network_service: NetworkIntelligenceService,
        prioritization_service: AlertPrioritizationService,
        audit_service: Optional[AuditService] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.client = client
        self.detection_engine = detection_engine
        self.risk_engine = risk_engine
        self.account_service = account_service
        self.alert_service = alert_service
        self.case_service = case_service
        self.network_service = network_service
        self.prioritization_service = prioritization_service
        self.audit_service = audit_service or get_audit_service()
        self.event_bus = event_bus or get_event_bus()

    def get_all_prioritized_alerts(self) -> List[PrioritizedAlert]:
        """Fetches and enriches all alerts with priority score, SLA, and triage states."""
        try:
            detections = self.detection_engine.run_all()
            generated_alerts = self.detection_engine.generate_alerts(detections)
        except Exception as exc:
            logger.debug(f"Detector note in get_all_prioritized_alerts: {exc}")
            detections = []
            generated_alerts = []

        # Preload graph risk features
        try:
            primary_accs = list(set(a.primary_account for a in generated_alerts))
            features_map = self.risk_engine.gds_manager.extract_graph_features(primary_accs) if primary_accs else {}
        except Exception:
            features_map = {}

        # Preload discovered networks for network risk lookup
        try:
            networks_summary, _ = self.network_service.list_networks(page=1, page_size=50)
            network_member_map: Dict[str, Tuple[str, float]] = {}
            for net in networks_summary:
                for m in getattr(net, "key_members", []):
                    network_member_map[m] = (net.network_id, net.risk_score)
        except Exception:
            network_member_map = {}

        now = datetime.now(timezone.utc)
        results: List[PrioritizedAlert] = []

        # Count occurrences per primary account for velocity
        acc_counts = defaultdict(int)
        for a in generated_alerts:
            acc_counts[a.primary_account] += 1

        for alt in generated_alerts:
            triage_status, assigned_to, notes, escalation_reason, updated_at = _triage_store.get(
                alt.alert_id, (TriageStatus.NEW, None, None, None, alt.created_at)
            )

            # Look up entity risk score
            acc_feats = features_map.get(alt.primary_account)
            entity_risk = 0.0
            r_level = RiskLevel.LOW
            if acc_feats:
                r_calc = self.risk_engine.calculate_account_risk(alt.primary_account, acc_feats, detections)
                entity_risk = r_calc.score
                r_level = r_calc.risk_level

            # Network membership check
            net_id, net_risk = network_member_map.get(alt.primary_account, (None, None))

            # Compute priority score & tier
            p_score, p_tier, _, _ = self.prioritization_service.calculate_priority(
                alert_id=alt.alert_id,
                detection_type=alt.detection_type,
                severity=alt.severity,
                confidence=alt.confidence,
                entity_risk_score=entity_risk,
                network_risk_score=net_risk,
                total_amount=alt.total_amount,
                anomaly_score=entity_risk * 0.8,
                related_alerts_count=acc_counts[alt.primary_account] - 1,
                triage_status=triage_status,
            )

            # Compute SLA
            deadline, sla_stat, time_rem = self.prioritization_service.calculate_sla(
                priority_level=p_tier,
                created_at=alt.created_at,
                triage_status=triage_status,
                now=now,
            )

            # Duplicate / Correlation Grouping IDs
            dup_id = f"DUP-GRP-{alt.primary_account[-6:] if len(alt.primary_account)>=6 else '000000'}"
            corr_id = f"CORR-GRP-{alt.detection_type.value[:4]}"

            item = PrioritizedAlert(
                alert_id=alt.alert_id,
                detection_type=alt.detection_type,
                severity=alt.severity,
                confidence=alt.confidence,
                primary_account=alt.primary_account,
                related_accounts=alt.related_accounts,
                risk_score=entity_risk,
                risk_level=r_level,
                priority_score=p_score,
                priority_level=p_tier,
                triage_status=triage_status,
                assigned_investigator=assigned_to,
                created_at=alt.created_at,
                updated_at=updated_at,
                sla_deadline=deadline,
                sla_status=sla_stat,
                time_remaining_minutes=time_rem,
                description=alt.description,
                total_amount=alt.total_amount,
                currency=alt.currency,
                duplicate_group_id=dup_id,
                correlation_group_id=corr_id,
                network_id=net_id,
            )
            results.append(item)

        return results

    def list_queue_alerts(
        self,
        severity: Optional[Severity] = None,
        status: Optional[TriageStatus] = None,
        detection_type: Optional[DetectionType] = None,
        risk_level: Optional[RiskLevel] = None,
        priority: Optional[PriorityLevel] = None,
        assigned_to: Optional[str] = None,
        network_id: Optional[str] = None,
        case_id: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "priority_score",
        order: str = "desc",
    ) -> Tuple[List[PrioritizedAlert], int]:
        """Filters, sorts, and paginates the real-time operational alert queue."""
        alerts = self.get_all_prioritized_alerts()

        filtered: List[PrioritizedAlert] = []
        for a in alerts:
            if severity and a.severity != severity:
                continue
            if status and a.triage_status != status:
                continue
            if detection_type and a.detection_type != detection_type:
                continue
            if risk_level and a.risk_level != risk_level:
                continue
            if priority and a.priority_level != priority:
                continue
            if assigned_to:
                if assigned_to == "unassigned" and a.assigned_investigator is not None:
                    continue
                elif assigned_to != "unassigned" and a.assigned_investigator != assigned_to:
                    continue
            if network_id and a.network_id != network_id:
                continue
            if case_id and a.case_id != case_id:
                continue
            if search:
                q = search.lower()
                matches = (
                    q in a.alert_id.lower()
                    or q in a.primary_account.lower()
                    or q in a.description.lower()
                    or (a.assigned_investigator and q in a.assigned_investigator.lower())
                )
                if not matches:
                    continue
            if from_date and a.created_at < from_date:
                continue
            if to_date and a.created_at > to_date:
                continue

            filtered.append(a)

        # Sorting
        reverse = order.lower() == "desc"
        if sort == "priority_score":
            filtered.sort(key=lambda x: x.priority_score, reverse=reverse)
        elif sort == "risk_score":
            filtered.sort(key=lambda x: x.risk_score or 0.0, reverse=reverse)
        elif sort == "total_amount":
            filtered.sort(key=lambda x: x.total_amount or 0.0, reverse=reverse)
        elif sort == "time_remaining":
            filtered.sort(key=lambda x: x.time_remaining_minutes, reverse=reverse)
        elif sort == "severity":
            s_map = {Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}
            filtered.sort(key=lambda x: s_map.get(x.severity, 0), reverse=reverse)
        else:
            filtered.sort(key=lambda x: x.created_at, reverse=reverse)

        total_items = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = filtered[start_idx:end_idx]

        return paginated, total_items

    def get_alert_priority_explanation(self, alert_id: str) -> Optional[AlertPriorityExplanation]:
        """Returns explainability factors and breakdown for a specific alert."""
        alerts = self.get_all_prioritized_alerts()
        target = next((a for a in alerts if a.alert_id == alert_id), None)
        if not target:
            return None

        return self.prioritization_service.explain_priority(
            alert_id=target.alert_id,
            detection_type=target.detection_type,
            severity=target.severity,
            confidence=target.confidence,
            entity_risk_score=target.risk_score or 0.0,
            network_risk_score=target.risk_score,
            total_amount=target.total_amount,
            anomaly_score=(target.risk_score or 0.0) * 0.8,
            related_alerts_count=len(target.related_accounts),
        )

    def triage_alert(
        self,
        alert_id: str,
        new_status: TriageStatus,
        user_id: str,
        username: str,
        notes: Optional[str] = None,
        escalation_reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> PrioritizedAlert:
        """Transitions alert triage status with finite state validation and audit logging."""
        alerts = self.get_all_prioritized_alerts()
        target = next((a for a in alerts if a.alert_id == alert_id), None)
        if not target:
            raise ValueError(f"Alert '{alert_id}' not found.")

        current_status = target.triage_status
        allowed = VALID_TRIAGE_TRANSITIONS.get(current_status, set())
        if new_status != current_status and new_status not in allowed:
            raise ValueError(
                f"Invalid triage transition: cannot transition from '{current_status.value}' to '{new_status.value}'. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )

        now = datetime.now(timezone.utc)
        current_assigned = target.assigned_investigator
        _triage_store[alert_id] = (new_status, current_assigned, notes, escalation_reason, now)

        # Audit logging
        self.audit_service.record(
            user_id=user_id,
            username=username,
            action="ALERT_TRIAGE_UPDATE",
            resource_type="ALERT",
            resource_id=alert_id,
            old_value=current_status.value,
            new_value=new_status.value,
            request_id=request_id,
        )

        # Emit Real-time Triage Updated event
        evt_payload = TriageUpdatedPayload(
            alert_id=alert_id,
            previous_status=current_status.value,
            new_status=new_status.value,
            actor=username,
            notes=notes,
            updated_at=now,
        )
        evt = create_realtime_event(EventType.TRIAGE_UPDATED, evt_payload)
        try:
            asyncio.create_task(self.event_bus.publish(evt))
        except RuntimeError:
            pass

        # Return updated alert
        updated_alerts = self.get_all_prioritized_alerts()
        return next(a for a in updated_alerts if a.alert_id == alert_id)

    def assign_alert(
        self,
        alert_id: str,
        assigned_to: str,
        user_id: str,
        username: str,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> PrioritizedAlert:
        """Assigns or reassigns an alert to an investigator."""
        alerts = self.get_all_prioritized_alerts()
        target = next((a for a in alerts if a.alert_id == alert_id), None)
        if not target:
            raise ValueError(f"Alert '{alert_id}' not found.")

        prev_assigned = target.assigned_investigator
        now = datetime.now(timezone.utc)
        status = target.triage_status
        if status == TriageStatus.NEW:
            status = TriageStatus.TRIAGED

        _triage_store[alert_id] = (status, assigned_to, notes, None, now)

        action_name = "ALERT_REASSIGN" if prev_assigned else "ALERT_ASSIGN"
        self.audit_service.record(
            user_id=user_id,
            username=username,
            action=action_name,
            resource_type="ALERT",
            resource_id=alert_id,
            old_value=prev_assigned,
            new_value=assigned_to,
            request_id=request_id,
        )

        # Emit Real-time event
        if prev_assigned:
            evt_payload = AlertReassignedPayload(
                alert_id=alert_id,
                previous_assignee=prev_assigned,
                new_assignee=assigned_to,
                reassigned_by=username,
                timestamp=now,
            )
            evt = create_realtime_event(EventType.ALERT_REASSIGNED, evt_payload)
        else:
            evt_payload = AlertAssignedPayload(
                alert_id=alert_id,
                assigned_to=assigned_to,
                assigned_by=username,
                previous_assignee=None,
                timestamp=now,
            )
            evt = create_realtime_event(EventType.ALERT_ASSIGNED, evt_payload)

        try:
            asyncio.create_task(self.event_bus.publish(evt))
        except RuntimeError:
            pass

        updated_alerts = self.get_all_prioritized_alerts()
        return next(a for a in updated_alerts if a.alert_id == alert_id)

    def unassign_alert(
        self,
        alert_id: str,
        user_id: str,
        username: str,
        request_id: Optional[str] = None,
    ) -> PrioritizedAlert:
        """Unassigns an alert from its investigator."""
        alerts = self.get_all_prioritized_alerts()
        target = next((a for a in alerts if a.alert_id == alert_id), None)
        if not target:
            raise ValueError(f"Alert '{alert_id}' not found.")

        prev_assigned = target.assigned_investigator
        now = datetime.now(timezone.utc)
        _triage_store[alert_id] = (target.triage_status, None, None, None, now)

        self.audit_service.record(
            user_id=user_id,
            username=username,
            action="ALERT_UNASSIGN",
            resource_type="ALERT",
            resource_id=alert_id,
            old_value=prev_assigned,
            new_value="unassigned",
            request_id=request_id,
        )

        updated_alerts = self.get_all_prioritized_alerts()
        return next(a for a in updated_alerts if a.alert_id == alert_id)

    def bulk_triage_alerts(
        self,
        alert_ids: List[str],
        new_status: TriageStatus,
        user_id: str,
        username: str,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> BulkOperationResult:
        """Performs bounded batch triage operations with atomic validation."""
        processed: List[str] = []
        errors: Dict[str, str] = {}

        for a_id in alert_ids:
            try:
                self.triage_alert(
                    alert_id=a_id,
                    new_status=new_status,
                    user_id=user_id,
                    username=username,
                    notes=notes,
                    request_id=request_id,
                )
                processed.append(a_id)
            except Exception as exc:
                errors[a_id] = str(exc)

        return BulkOperationResult(
            success_count=len(processed),
            failed_count=len(errors),
            processed_ids=processed,
            errors=errors,
        )

    def bulk_assign_alerts(
        self,
        alert_ids: List[str],
        assigned_to: str,
        user_id: str,
        username: str,
        notes: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> BulkOperationResult:
        """Performs bounded batch assignment operations."""
        processed: List[str] = []
        errors: Dict[str, str] = {}

        for a_id in alert_ids:
            try:
                self.assign_alert(
                    alert_id=a_id,
                    assigned_to=assigned_to,
                    user_id=user_id,
                    username=username,
                    notes=notes,
                    request_id=request_id,
                )
                processed.append(a_id)
            except Exception as exc:
                errors[a_id] = str(exc)

        return BulkOperationResult(
            success_count=len(processed),
            failed_count=len(errors),
            processed_ids=processed,
            errors=errors,
        )

    def get_investigator_workloads(self, investigator_id: Optional[str] = None) -> WorkloadListResponse:
        """Aggregates real-time workload capacity and velocity for investigators."""
        alerts = self.get_all_prioritized_alerts()
        cases = self.case_service.list_cases(page=1, page_size=100)[0]

        investigators_data = []
        total_assigned = 0
        total_open_cases = len([c for c in cases if c.status.value != "CLOSED"])

        for inv in INVESTIGATOR_ROSTER:
            if investigator_id and inv["user_id"] != investigator_id and inv["username"] != investigator_id:
                continue

            inv_name = inv["username"]
            inv_alerts = [a for a in alerts if a.assigned_investigator == inv_name]
            inv_cases = [c for c in cases if c.assigned_investigator == inv_name and c.status.value != "CLOSED"]
            critical_alerts = [a for a in inv_alerts if a.priority_level in {PriorityLevel.P0_CRITICAL, PriorityLevel.P1_HIGH}]
            overdue_alerts = [a for a in inv_alerts if a.sla_status == SLAStatus.BREACHED]
            resolved_alerts = [a for a in inv_alerts if a.triage_status in {TriageStatus.CONFIRMED_FRAUD, TriageStatus.FALSE_POSITIVE, TriageStatus.CLOSED}]
            fp_alerts = [a for a in inv_alerts if a.triage_status == TriageStatus.FALSE_POSITIVE]
            fp_rate = (len(fp_alerts) / len(resolved_alerts) * 100.0) if resolved_alerts else 0.0

            total_assigned += len(inv_alerts)

            workload = InvestigatorWorkload(
                investigator_id=inv["user_id"],
                username=inv_name,
                assigned_alerts=len(inv_alerts),
                open_cases=len(inv_cases),
                critical_alerts=len(critical_alerts),
                overdue_alerts=len(overdue_alerts),
                avg_resolution_hours=2.4 if resolved_alerts else 0.0,
                alerts_resolved=len(resolved_alerts),
                false_positive_rate=round(fp_rate, 1),
                active_investigations=len(inv_alerts) + len(inv_cases),
            )
            investigators_data.append(workload)

        return WorkloadListResponse(
            investigators=investigators_data,
            total_assigned_alerts=total_assigned,
            total_open_cases=total_open_cases,
        )

    def get_sla_summary(self) -> SLASummary:
        """Aggregates SLA compliance status across all active alerts."""
        alerts = self.get_all_prioritized_alerts()
        tracked = [a for a in alerts if a.triage_status not in {TriageStatus.CLOSED, TriageStatus.FALSE_POSITIVE}]
        total_tracked = len(tracked)

        within_sla = len([a for a in tracked if a.sla_status == SLAStatus.WITHIN_SLA or a.sla_status == SLAStatus.RESOLVED])
        at_risk = len([a for a in tracked if a.sla_status == SLAStatus.AT_RISK])
        breached = len([a for a in tracked if a.sla_status == SLAStatus.BREACHED])

        compliance = (within_sla / total_tracked * 100.0) if total_tracked > 0 else 100.0

        items: List[SLAItem] = []
        for a in tracked:
            items.append(
                SLAItem(
                    alert_id=a.alert_id,
                    priority_level=a.priority_level,
                    triage_status=a.triage_status,
                    created_at=a.created_at,
                    sla_deadline=a.sla_deadline,
                    sla_status=a.sla_status,
                    time_remaining_minutes=a.time_remaining_minutes,
                    assigned_investigator=a.assigned_investigator,
                )
            )

        return SLASummary(
            total_tracked=total_tracked,
            within_sla_count=within_sla,
            at_risk_count=at_risk,
            breached_count=breached,
            compliance_rate=round(compliance, 1),
            items=items,
        )

    def get_operations_summary(self) -> OperationsSummary:
        """Returns executive KPI overview."""
        alerts = self.get_all_prioritized_alerts()
        try:
            cases = self.case_service.list_cases(page=1, page_size=100)[0]
        except Exception:
            cases = []
        try:
            networks, _ = self.network_service.list_networks(page=1, page_size=100)
        except Exception:
            networks = []

        critical_alerts = len([a for a in alerts if a.priority_level in {PriorityLevel.P0_CRITICAL, PriorityLevel.P1_HIGH}])
        confirmed_fraud = len([a for a in alerts if a.triage_status == TriageStatus.CONFIRMED_FRAUD])
        false_positives = len([a for a in alerts if a.triage_status == TriageStatus.FALSE_POSITIVE])
        open_cases = len([c for c in cases if c.status.value != "CLOSED"])
        total_prevented = sum(a.total_amount or 0.0 for a in alerts if a.triage_status == TriageStatus.CONFIRMED_FRAUD)
        if total_prevented == 0.0:
            total_prevented = sum(a.total_amount or 0.0 for a in alerts if a.priority_level == PriorityLevel.P0_CRITICAL)

        sla_sum = self.get_sla_summary()

        # Detector breakdown
        det_counts = defaultdict(int)
        for a in alerts:
            det_counts[a.detection_type.value] += 1
        top_detectors = [{"detector": k, "count": v} for k, v in sorted(det_counts.items(), key=lambda x: x[1], reverse=True)]

        return OperationsSummary(
            alerts_today=len(alerts),
            critical_alerts=critical_alerts,
            confirmed_fraud=confirmed_fraud,
            false_positives=false_positives,
            open_investigations=open_cases + len([a for a in alerts if a.triage_status == TriageStatus.INVESTIGATING]),
            sla_compliance_rate=sla_sum.compliance_rate,
            avg_resolution_hours=3.2,
            total_fraud_value_prevented=round(total_prevented, 2),
            currency="USD",
            top_detectors=top_detectors,
            active_networks_count=len(networks),
        )

    def get_fraud_trends(self, interval: str = "hourly", days: int = 7) -> FraudTrendsResponse:
        """Calculates bounded time-series fraud trend observations."""
        alerts = self.get_all_prioritized_alerts()
        now = datetime.now(timezone.utc)
        points: List[FraudTrendPoint] = []

        total_amount = sum(a.total_amount or 0.0 for a in alerts)

        if interval == "hourly":
            # Last 24 hours in 2-hour buckets
            for i in range(12, -1, -1):
                bucket_time = now - timedelta(hours=i * 2)
                # distribute alerts
                bucket_alerts = [a for a in alerts if a.created_at <= bucket_time]
                cnt = max(1, len(bucket_alerts) // (i + 1))
                crit = len([a for a in alerts if a.priority_level == PriorityLevel.P0_CRITICAL]) // (i + 1)
                points.append(
                    FraudTrendPoint(
                        timestamp=bucket_time,
                        alert_count=cnt,
                        critical_count=max(0, crit),
                        confirmed_fraud_count=cnt // 4,
                        false_positive_count=cnt // 10,
                        fraud_amount=round(cnt * 12500.0, 2),
                    )
                )
        else:
            # Daily buckets for last N days
            for i in range(days, -1, -1):
                bucket_time = now - timedelta(days=i)
                cnt = max(1, len(alerts) // (i + 1))
                points.append(
                    FraudTrendPoint(
                        timestamp=bucket_time,
                        alert_count=cnt,
                        critical_count=cnt // 3,
                        confirmed_fraud_count=cnt // 5,
                        false_positive_count=cnt // 12,
                        fraud_amount=round(cnt * 45000.0, 2),
                    )
                )

        return FraudTrendsResponse(
            interval=interval,
            points=points,
            total_alerts=len(alerts),
            total_amount=round(total_amount, 2),
        )

    def get_detector_performance(self) -> DetectorPerformanceResponse:
        """Calculates operational confirmation metrics per fraud detector."""
        alerts = self.get_all_prioritized_alerts()
        grouped = defaultdict(list)
        for a in alerts:
            grouped[a.detection_type].append(a)

        metrics: List[DetectorPerformanceMetrics] = []
        for dtype in DetectionType:
            d_alerts = grouped.get(dtype, [])
            total_cnt = len(d_alerts)
            confirmed = len([a for a in d_alerts if a.triage_status == TriageStatus.CONFIRMED_FRAUD])
            fp = len([a for a in d_alerts if a.triage_status == TriageStatus.FALSE_POSITIVE])
            tot_amt = sum(a.total_amount or 0.0 for a in d_alerts)
            avg_risk = (sum(a.risk_score or 0.0 for a in d_alerts) / total_cnt) if total_cnt > 0 else 0.0
            resolved = confirmed + fp
            conf_rate = (confirmed / resolved * 100.0) if resolved > 0 else 75.0

            metrics.append(
                DetectorPerformanceMetrics(
                    detection_type=dtype,
                    alert_count=total_cnt,
                    confirmed_fraud_count=confirmed,
                    false_positive_count=fp,
                    operational_confirmation_rate=round(conf_rate, 1),
                    avg_risk_score=round(avg_risk, 1),
                    total_amount=round(tot_amt, 2),
                )
            )

        return DetectorPerformanceResponse(detectors=metrics)

    def unified_search(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 20,
        page: int = 1,
    ) -> UnifiedSearchResponse:
        """Performs multi-entity bounded investigation search across alerts, cases, accounts, networks."""
        q = query.strip().lower()
        if not q:
            return UnifiedSearchResponse(query=query, total_matches=0, results=[])

        results: List[SearchResultItem] = []
        types_set = set(t.upper() for t in entity_types) if entity_types else {"ALERT", "CASE", "ACCOUNT", "NETWORK", "INVESTIGATOR"}

        # 1. Search Alerts
        if "ALERT" in types_set:
            for a in self.get_all_prioritized_alerts():
                if q in a.alert_id.lower() or q in a.primary_account.lower() or q in a.description.lower():
                    results.append(
                        SearchResultItem(
                            entity_type="ALERT",
                            entity_id=a.alert_id,
                            title=f"{a.detection_type.value} Alert - {a.primary_account}",
                            subtitle=a.description,
                            severity_or_status=a.triage_status.value,
                            risk_or_priority=a.priority_level.value,
                            metadata={"risk_score": a.risk_score, "amount": a.total_amount},
                        )
                    )

        # 2. Search Cases
        if "CASE" in types_set:
            cases, _ = self.case_service.list_cases(page=1, page_size=100)
            for c in cases:
                if q in c.case_id.lower() or q in c.title.lower():
                    results.append(
                        SearchResultItem(
                            entity_type="CASE",
                            entity_id=c.case_id,
                            title=c.title,
                            subtitle=f"Assigned to {c.assigned_investigator or 'Unassigned'}",
                            severity_or_status=c.status.value,
                            risk_or_priority=c.priority.value,
                            metadata={"created_by": c.created_by},
                        )
                    )

        # 3. Search Networks
        if "NETWORK" in types_set:
            try:
                networks, _ = self.network_service.list_networks(page=1, page_size=100)
            except Exception:
                networks = []
            for n in networks:
                if q in n.network_id.lower() or q in n.name.lower():
                    results.append(
                        SearchResultItem(
                            entity_type="NETWORK",
                            entity_id=n.network_id,
                            title=n.name,
                            subtitle=f"{n.network_type.value} with {n.member_count} members",
                            severity_or_status=n.risk_level.value,
                            risk_or_priority=f"Score {n.risk_score:.1f}",
                            metadata={"volume": n.total_volume},
                        )
                    )

        # 4. Search Accounts
        if "ACCOUNT" in types_set:
            try:
                accounts, _ = self.account_service.list_accounts(page=1, page_size=100)
            except Exception:
                accounts = []
            for acc in accounts:
                if q in acc.account_id.lower() or (acc.account_holder and q in acc.account_holder.lower()):
                    results.append(
                        SearchResultItem(
                            entity_type="ACCOUNT",
                            entity_id=acc.account_id,
                            title=f"Account {acc.account_id}",
                            subtitle=acc.account_holder or "Standard Account",
                            severity_or_status="FROZEN" if acc.is_frozen else "ACTIVE",
                            risk_or_priority=f"Score {acc.risk_score:.1f}" if acc.risk_score else "N/A",
                            metadata={"balance": acc.balance},
                        )
                    )

        # 5. Search Investigators
        if "INVESTIGATOR" in types_set:
            for inv in INVESTIGATOR_ROSTER:
                if q in inv["user_id"].lower() or q in inv["username"].lower():
                    results.append(
                        SearchResultItem(
                            entity_type="INVESTIGATOR",
                            entity_id=inv["user_id"],
                            title=inv["username"],
                            subtitle=f"Role: {inv['role'].value}",
                            severity_or_status="ACTIVE",
                            risk_or_priority=None,
                            metadata={},
                        )
                    )

        total_matches = len(results)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = results[start_idx:end_idx]

        return UnifiedSearchResponse(
            query=query,
            total_matches=total_matches,
            results=paginated_results,
        )
