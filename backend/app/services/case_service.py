"""
FinGraph Case Management & Evidence Service.
Provides thread-safe in-memory case lifecycle management, evidence registration
with cryptographic SHA-256 integrity verification, note threads, and audit trail recording.
"""
import asyncio
import hashlib
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.app.models.cases import (
    CaseCreateRequest,
    CasePriority,
    CaseStatus,
    CaseUpdateRequest,
    EvidenceCreateRequest,
    EvidenceItem,
    EvidenceType,
    InvestigationCase,
    InvestigationCaseSummary,
    InvestigationNote,
)
from backend.app.models.intelligence import InvestigationTimelineEvent, TimelineEventType
from backend.app.realtime.event_bus import get_event_bus
from backend.app.realtime.events import (
    CaseCreatedPayload,
    CaseUpdatedPayload,
    EventType,
    InvestigationUpdatedPayload,
    create_realtime_event,
)

logger = logging.getLogger("FinGraph.CaseService")

ALLOWED_CASE_TRANSITIONS = {
    CaseStatus.OPEN: {CaseStatus.IN_PROGRESS, CaseStatus.RESOLVED, CaseStatus.CLOSED},
    CaseStatus.IN_PROGRESS: {CaseStatus.ESCALATED, CaseStatus.RESOLVED, CaseStatus.CLOSED},
    CaseStatus.ESCALATED: {CaseStatus.IN_PROGRESS, CaseStatus.RESOLVED, CaseStatus.CLOSED},
    CaseStatus.RESOLVED: {CaseStatus.IN_PROGRESS, CaseStatus.CLOSED},
    CaseStatus.CLOSED: {CaseStatus.IN_PROGRESS},
}


def _publish_event_safe(event):
    """Dispatches real-time event without raising or blocking synchronous code."""
    try:
        event_bus = get_event_bus()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(event_bus.publish(event))
        except RuntimeError:
            pass
    except Exception as exc:
        logger.debug(f"Event dispatch note: {exc}")


class CaseService:
    """Service managing fraud investigation cases, evidence items, and notes."""

    def __init__(self):
        self._lock = threading.RLock()
        self._cases: Dict[str, InvestigationCase] = {}
        self._seed_default_cases()

    def _seed_default_cases(self) -> None:
        """Seeds realistic initial cases for interactive investigation triage."""
        with self._lock:
            if self._cases:
                return

            c1 = InvestigationCase(
                case_id="CASE-2026-001",
                title="Syndicate Circular Wash Trading (Loop A001-A004)",
                description="High-velocity cyclic funds movement detected across 4 commercial accounts. Rapid dispersion follows circular routing.",
                priority=CasePriority.CRITICAL,
                status=CaseStatus.IN_PROGRESS,
                assigned_investigator="investigator",
                linked_alerts=["ALT-CIRCULAR-01", "ALT-001"],
                linked_accounts=["A001", "A002", "A003", "A004"],
                linked_transactions=["TX_001", "TX_002", "TX_003", "TX_004"],
                notes=[
                    InvestigationNote(
                        note_id="NOTE-001",
                        author_id="usr_inv",
                        author_name="investigator",
                        content="Initiated forensic path tracing. Found 100% round-trip volume matching Pattern D circular loop.",
                    )
                ],
                evidence=[
                    EvidenceItem(
                        evidence_id="EVD-001",
                        case_id="CASE-2026-001",
                        type=EvidenceType.GRAPH_PATH,
                        source="Neo4j Cypher Engine",
                        related_entity="A001",
                        title="Circular Wash Cycle Path",
                        description="4-node closed directed cycle: A001 -> A002 -> A003 -> A004 -> A001.",
                        data={"cycle_length": 4, "nodes": ["A001", "A002", "A003", "A004"]},
                        created_by="investigator",
                        integrity_hash=hashlib.sha256(b"A001->A002->A003->A004->A001").hexdigest(),
                    )
                ],
                created_by="investigator",
            )

            c2 = InvestigationCase(
                case_id="CASE-2026-002",
                title="Funnel Smurfing Inflow into Mule Hub A015",
                description="Aggregated multi-party micro-deposits totaling $48,000 consolidated into intermediary mule account within 10 minutes.",
                priority=CasePriority.HIGH,
                status=CaseStatus.OPEN,
                assigned_investigator="investigator",
                linked_alerts=["ALT-FUNNEL-01"],
                linked_accounts=["A015", "A010", "A011", "A012"],
                linked_transactions=["TX_015_IN1", "TX_015_IN2"],
                notes=[],
                evidence=[],
                created_by="admin",
            )

            self._cases[c1.case_id] = c1
            self._cases[c2.case_id] = c2

    def create_case(
        self,
        req: CaseCreateRequest,
        author_id: str,
        author_name: str,
    ) -> InvestigationCase:
        """Creates and registers a new investigation case."""
        with self._lock:
            case = InvestigationCase(
                title=req.title,
                description=req.description,
                priority=req.priority,
                status=CaseStatus.OPEN,
                assigned_investigator=req.assigned_investigator or author_name,
                linked_alerts=req.linked_alerts,
                linked_accounts=req.linked_accounts,
                linked_transactions=req.linked_transactions,
                created_by=author_name,
            )
            self._cases[case.case_id] = case

        # Emit realtime event safely
        event = create_realtime_event(
            EventType.CASE_CREATED,
            CaseCreatedPayload(
                case_id=case.case_id,
                title=case.title,
                priority=case.priority.value,
                status=case.status.value,
                assigned_investigator=case.assigned_investigator,
                created_by=case.created_by,
                created_at=case.created_at,
            ),
        )
        _publish_event_safe(event)

        return case

    def get_case_by_id(self, case_id: str) -> Optional[InvestigationCase]:
        """Retrieves a single case record by ID."""
        with self._lock:
            return self._cases.get(case_id)

    def list_cases(
        self,
        status: Optional[CaseStatus] = None,
        priority: Optional[CasePriority] = None,
        assigned_to: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[InvestigationCaseSummary], int]:
        """Lists cases matching filter criteria with pagination."""
        with self._lock:
            all_cases = list(self._cases.values())

        # Filtering
        filtered = []
        for c in all_cases:
            if status and c.status != status:
                continue
            if priority and c.priority != priority:
                continue
            if assigned_to and c.assigned_investigator != assigned_to:
                continue
            if search:
                q = search.lower()
                if (
                    q not in c.case_id.lower()
                    and q not in c.title.lower()
                    and q not in c.description.lower()
                    and not any(q in acc.lower() for acc in c.linked_accounts)
                ):
                    continue
            filtered.append(c)

        filtered.sort(key=lambda x: x.updated_at, reverse=True)
        total = len(filtered)

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        sliced = filtered[start_idx:end_idx]

        summaries = [
            InvestigationCaseSummary(
                case_id=c.case_id,
                title=c.title,
                priority=c.priority,
                status=c.status,
                assigned_investigator=c.assigned_investigator,
                alerts_count=len(c.linked_alerts),
                accounts_count=len(c.linked_accounts),
                notes_count=len(c.notes),
                evidence_count=len(c.evidence),
                created_at=c.created_at,
                updated_at=c.updated_at,
                created_by=c.created_by,
            )
            for c in sliced
        ]

        return summaries, total

    def update_case(
        self,
        case_id: str,
        update_req: CaseUpdateRequest,
        actor_name: str,
    ) -> Optional[InvestigationCase]:
        """Modifies title, description, priority, or status for a case."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None

            if update_req.title is not None:
                case.title = update_req.title
            if update_req.description is not None:
                case.description = update_req.description
            if update_req.priority is not None:
                case.priority = update_req.priority
            if update_req.status is not None:
                case.status = update_req.status

            case.updated_at = datetime.now(timezone.utc)

        event = create_realtime_event(
            EventType.CASE_UPDATED,
            CaseUpdatedPayload(
                case_id=case.case_id,
                status=case.status.value,
                priority=case.priority.value,
                assigned_investigator=case.assigned_investigator,
                updated_at=case.updated_at,
                action="UPDATE",
            ),
        )
        _publish_event_safe(event)

        return case

    def assign_investigator(
        self,
        case_id: str,
        investigator: str,
        actor_name: str,
    ) -> Optional[InvestigationCase]:
        """Assigns or transfers a case to a specific investigator."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None

            case.assigned_investigator = investigator
            case.updated_at = datetime.now(timezone.utc)

        event = create_realtime_event(
            EventType.CASE_UPDATED,
            CaseUpdatedPayload(
                case_id=case.case_id,
                status=case.status.value,
                priority=case.priority.value,
                assigned_investigator=case.assigned_investigator,
                updated_at=case.updated_at,
                action="REASSIGN",
            ),
        )
        _publish_event_safe(event)

        return case

    def add_note(
        self,
        case_id: str,
        content: str,
        author_id: str,
        author_name: str,
    ) -> Optional[InvestigationNote]:
        """Appends a new investigation note to the case note thread."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None

            note = InvestigationNote(
                author_id=author_id,
                author_name=author_name,
                content=content,
            )
            case.notes.append(note)
            case.updated_at = datetime.now(timezone.utc)

        event = create_realtime_event(
            EventType.INVESTIGATION_UPDATED,
            InvestigationUpdatedPayload(
                case_id=case_id,
                update_type="NOTE_ADDED",
                author=author_name,
                timestamp=note.created_at,
                detail=f"Note added by {author_name}",
            ),
        )
        _publish_event_safe(event)

        return note

    def add_evidence(
        self,
        case_id: str,
        req: EvidenceCreateRequest,
        author_id: str,
        author_name: str,
    ) -> Optional[EvidenceItem]:
        """Registers a forensic evidence item with cryptographic SHA-256 hash."""
        raw_bytes = json.dumps(
            {"type": req.type.value, "title": req.title, "entity": req.related_entity, "data": req.data},
            sort_keys=True,
        ).encode("utf-8")
        integrity_hash = hashlib.sha256(raw_bytes).hexdigest()

        evidence = EvidenceItem(
            case_id=case_id,
            type=req.type,
            source=req.source,
            related_entity=req.related_entity,
            title=req.title,
            description=req.description,
            data=req.data,
            created_by=author_name,
            integrity_hash=integrity_hash,
        )

        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            case.evidence.append(evidence)
            case.updated_at = datetime.now(timezone.utc)

        event = create_realtime_event(
            EventType.INVESTIGATION_UPDATED,
            InvestigationUpdatedPayload(
                case_id=case_id,
                update_type="EVIDENCE_ATTACHED",
                author=author_name,
                timestamp=evidence.created_at,
                detail=f"Evidence '{evidence.title}' attached ({evidence.type.value})",
            ),
        )
        _publish_event_safe(event)

        return evidence

    def link_alert(self, case_id: str, alert_id: str, actor_name: str) -> Optional[InvestigationCase]:
        """Associates an alert ID with a case."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            if alert_id not in case.linked_alerts:
                case.linked_alerts.append(alert_id)
                case.updated_at = datetime.now(timezone.utc)
        return case

    def unlink_alert(self, case_id: str, alert_id: str, actor_name: str) -> Optional[InvestigationCase]:
        """Removes an alert association from a case."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            if alert_id in case.linked_alerts:
                case.linked_alerts.remove(alert_id)
                case.updated_at = datetime.now(timezone.utc)
        return case

    def link_account(self, case_id: str, account_id: str, actor_name: str) -> Optional[InvestigationCase]:
        """Associates an account ID with a case."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            if account_id not in case.linked_accounts:
                case.linked_accounts.append(account_id)
                case.updated_at = datetime.now(timezone.utc)
        return case

    def unlink_account(self, case_id: str, account_id: str, actor_name: str) -> Optional[InvestigationCase]:
        """Removes an account association from a case."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            if account_id in case.linked_accounts:
                case.linked_accounts.remove(account_id)
                case.updated_at = datetime.now(timezone.utc)
        return case

    def get_case_timeline(self, case_id: str) -> List[InvestigationTimelineEvent]:
        """Constructs a chronological event feed for a case."""
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return []

        events: List[InvestigationTimelineEvent] = []

        events.append(
            InvestigationTimelineEvent(
                timestamp=case.created_at,
                event_type=TimelineEventType.CASE_CREATED,
                actor=case.created_by,
                entity_id=case.case_id,
                title="Case Opened",
                description=f"Investigation case '{case.title}' created with priority {case.priority.value}.",
                metadata={"priority": case.priority.value, "status": case.status.value},
            )
        )

        for n in case.notes:
            events.append(
                InvestigationTimelineEvent(
                    timestamp=n.created_at,
                    event_type=TimelineEventType.INVESTIGATION_NOTE,
                    actor=n.author_name,
                    entity_id=case.case_id,
                    title=f"Note Added by {n.author_name}",
                    description=n.content,
                    metadata={"note_id": n.note_id},
                )
            )

        for e in case.evidence:
            events.append(
                InvestigationTimelineEvent(
                    timestamp=e.created_at,
                    event_type=TimelineEventType.EVIDENCE_ATTACHED,
                    actor=e.created_by,
                    entity_id=case.case_id,
                    title=f"Evidence Attached: {e.title}",
                    description=e.description or f"Attached {e.type.value} from {e.source}",
                    evidence_ref=e.evidence_id,
                    metadata={"type": e.type.value, "hash": e.integrity_hash},
                )
            )

        events.sort(key=lambda x: x.timestamp)
        return events


_global_case_service: Optional[CaseService] = None


def get_case_service() -> CaseService:
    """Singleton getter for CaseService."""
    global _global_case_service
    if _global_case_service is None:
        _global_case_service = CaseService()
    return _global_case_service
