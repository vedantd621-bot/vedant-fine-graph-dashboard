"""
Tests for Investigation Task & Checklist Management in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.tasks import InvestigationTaskManager
from backend.app.intelligence_orchestration.models import (
    TaskStatus,
    PriorityBand,
    TaskCreateRequest,
    TaskUpdateRequest,
    ChecklistItemCreateRequest,
    ChecklistItemUpdateRequest,
)
from backend.app.intelligence_orchestration.exceptions import TaskNotFoundError

@pytest.fixture
def task_manager():
    return InvestigationTaskManager()

def test_create_and_update_task(task_manager):
    req = TaskCreateRequest(
        case_id="CASE-2026-001",
        title="Inspect IP Logins",
        description="Check proxy subnets",
        priority=PriorityBand.HIGH,
        assignee="analyst_1",
    )
    task = task_manager.create_task(req, creator_id="usr_admin")
    assert task.task_id.startswith("tsk_")
    assert task.status == TaskStatus.OPEN
    assert task.assignee == "analyst_1"
    
    # Update task
    update_req = TaskUpdateRequest(status=TaskStatus.COMPLETED, priority=PriorityBand.CRITICAL)
    updated = task_manager.update_task(task.task_id, update_req, actor_id="usr_admin")
    assert updated.status == TaskStatus.COMPLETED
    assert updated.priority == PriorityBand.CRITICAL
    assert updated.completed_at is not None

def test_task_not_found(task_manager):
    with pytest.raises(TaskNotFoundError):
        task_manager.get_task("tsk_non_existent")

def test_case_checklist_crud(task_manager):
    items = task_manager.get_checklist("CASE-2026-001")
    assert len(items) >= 5
    
    # Add item
    new_item = task_manager.add_checklist_item("CASE-2026-001", ChecklistItemCreateRequest(title="Conduct Audio Triage", order=6))
    assert new_item.title == "Conduct Audio Triage"
    
    # Toggle item
    toggled = task_manager.update_checklist_item("CASE-2026-001", new_item.item_id, ChecklistItemUpdateRequest(is_completed=True), actor_id="usr_lead")
    assert toggled.is_completed is True
    assert toggled.completed_by == "usr_lead"
