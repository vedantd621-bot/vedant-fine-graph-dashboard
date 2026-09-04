"""
FinGraph Investigation Task & Checklist Management Engine.
Maintains task lifecycle, assignee routing, and interactive case checklists.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid

from backend.app.intelligence_orchestration.exceptions import TaskNotFoundError
from backend.app.intelligence_orchestration.models import (
    CaseChecklistItem,
    ChecklistItemCreateRequest,
    ChecklistItemUpdateRequest,
    InvestigationTask,
    PriorityBand,
    TaskCreateRequest,
    TaskStatus,
    TaskUpdateRequest,
)


class InvestigationTaskManager:
    """
    Manages investigator task assignments and case checklist progress.
    """

    def __init__(self):
        self._tasks: Dict[str, InvestigationTask] = {}
        self._checklists: Dict[str, List[CaseChecklistItem]] = {}
        self._seed_initial_tasks()

    def _seed_initial_tasks(self) -> None:
        t1 = InvestigationTask(
            task_id="tsk_001",
            case_id="CASE-2026-001",
            title="Inspect Canvas Device Fingerprint Collision",
            description="Verify if fp_ghost_99a is associated with known proxy subnets.",
            priority=PriorityBand.HIGH,
            assignee="investigator",
            status=TaskStatus.IN_PROGRESS,
            created_by="system",
            created_at=datetime.now(timezone.utc),
        )
        t2 = InvestigationTask(
            task_id="tsk_002",
            case_id="CASE-2026-001",
            title="Beneficiary KYC & Outbound Settlement Review",
            description="Review identity documentation for recipient acc_882.",
            priority=PriorityBand.CRITICAL,
            assignee="investigator",
            status=TaskStatus.OPEN,
            created_by="system",
            created_at=datetime.now(timezone.utc),
        )
        self._tasks[t1.task_id] = t1
        self._tasks[t2.task_id] = t2

        self._checklists["CASE-2026-001"] = [
            CaseChecklistItem(case_id="CASE-2026-001", title="Review transaction history and velocity", is_completed=True, order=1),
            CaseChecklistItem(case_id="CASE-2026-001", title="Verify connected counterparty accounts", is_completed=True, order=2),
            CaseChecklistItem(case_id="CASE-2026-001", title="Inspect shared hardware & IP attributes", is_completed=True, order=3),
            CaseChecklistItem(case_id="CASE-2026-001", title="Assess coordinated campaign membership", is_completed=False, order=4),
            CaseChecklistItem(case_id="CASE-2026-001", title="Submit final forensic decision", is_completed=False, order=5),
        ]

    def create_task(self, request: TaskCreateRequest, creator_id: str) -> InvestigationTask:
        task = InvestigationTask(
            case_id=request.case_id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            assignee=request.assignee,
            created_by=creator_id,
            due_at=request.due_at,
            evidence_refs=request.evidence_refs,
        )
        self._tasks[task.task_id] = task
        return task

    def update_task(self, task_id: str, request: TaskUpdateRequest, actor_id: str) -> InvestigationTask:
        if task_id not in self._tasks:
            raise TaskNotFoundError(f"Task '{task_id}' was not found.")
        t = self._tasks[task_id]
        if request.title is not None:
            t.title = request.title
        if request.description is not None:
            t.description = request.description
        if request.priority is not None:
            t.priority = request.priority
        if request.assignee is not None:
            t.assignee = request.assignee
        if request.due_at is not None:
            t.due_at = request.due_at
        if request.status is not None:
            t.status = request.status
            if request.status == TaskStatus.COMPLETED:
                t.completed_at = datetime.now(timezone.utc)
        return t

    def get_task(self, task_id: str) -> InvestigationTask:
        if task_id not in self._tasks:
            raise TaskNotFoundError(f"Task '{task_id}' was not found.")
        return self._tasks[task_id]

    def list_tasks(
        self,
        case_id: Optional[str] = None,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[InvestigationTask]:
        tasks = list(self._tasks.values())
        if case_id:
            tasks = [t for t in tasks if t.case_id == case_id]
        if assignee:
            tasks = [t for t in tasks if t.assignee.lower() == assignee.lower()]
        if status:
            tasks = [t for t in tasks if t.status.value.upper() == status.upper()]
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)

    def get_checklist(self, case_id: str) -> List[CaseChecklistItem]:
        if case_id not in self._checklists:
            self._checklists[case_id] = [
                CaseChecklistItem(case_id=case_id, title="Review transaction history and velocity", is_completed=False, order=1),
                CaseChecklistItem(case_id=case_id, title="Verify connected counterparty accounts", is_completed=False, order=2),
                CaseChecklistItem(case_id=case_id, title="Inspect shared hardware & IP attributes", is_completed=False, order=3),
                CaseChecklistItem(case_id=case_id, title="Assess coordinated campaign membership", is_completed=False, order=4),
                CaseChecklistItem(case_id=case_id, title="Submit final forensic decision", is_completed=False, order=5),
            ]
        return sorted(self._checklists[case_id], key=lambda x: x.order)

    def add_checklist_item(self, case_id: str, request: ChecklistItemCreateRequest) -> CaseChecklistItem:
        items = self.get_checklist(case_id)
        new_item = CaseChecklistItem(
            case_id=case_id,
            title=request.title,
            order=request.order or (len(items) + 1),
        )
        items.append(new_item)
        self._checklists[case_id] = items
        return new_item

    def update_checklist_item(
        self,
        case_id: str,
        item_id: str,
        request: ChecklistItemUpdateRequest,
        actor_id: str,
    ) -> CaseChecklistItem:
        items = self.get_checklist(case_id)
        target = next((i for i in items if i.item_id == item_id), None)
        if not target:
            raise TaskNotFoundError(f"Checklist item '{item_id}' not found for case '{case_id}'.")
        target.is_completed = request.is_completed
        target.completed_by = actor_id if request.is_completed else None
        target.completed_at = datetime.now(timezone.utc) if request.is_completed else None
        return target
