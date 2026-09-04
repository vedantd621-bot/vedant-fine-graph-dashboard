"""
Tests for Workflow Templates & State Machine in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.workflows import (
    WorkflowStateMachine,
    WorkflowTemplateRegistry,
)
from backend.app.intelligence_orchestration.models import WorkflowState, WorkflowType
from backend.app.intelligence_orchestration.exceptions import (
    InvalidWorkflowTransitionError,
    TemplateNotFoundError,
)

@pytest.fixture
def state_machine():
    return WorkflowStateMachine()

@pytest.fixture
def template_registry():
    return WorkflowTemplateRegistry()

def test_legal_workflow_transitions(state_machine):
    # Valid flow: CREATED -> TRIAGED -> INVESTIGATING -> EVIDENCE_REVIEW -> DECISION_PENDING -> DECIDED -> CLOSED
    state_machine.validate_transition(WorkflowState.CREATED, WorkflowState.TRIAGED)
    state_machine.validate_transition(WorkflowState.TRIAGED, WorkflowState.INVESTIGATING)
    state_machine.validate_transition(WorkflowState.INVESTIGATING, WorkflowState.EVIDENCE_REVIEW)
    state_machine.validate_transition(WorkflowState.EVIDENCE_REVIEW, WorkflowState.DECISION_PENDING)
    state_machine.validate_transition(WorkflowState.DECISION_PENDING, WorkflowState.DECIDED)
    state_machine.validate_transition(WorkflowState.DECIDED, WorkflowState.CLOSED)
    
    # Reopen flow: CLOSED -> INVESTIGATING
    state_machine.validate_transition(WorkflowState.CLOSED, WorkflowState.INVESTIGATING)

def test_illegal_workflow_transitions(state_machine):
    with pytest.raises(InvalidWorkflowTransitionError):
        state_machine.validate_transition(WorkflowState.CREATED, WorkflowState.DECIDED)
    with pytest.raises(InvalidWorkflowTransitionError):
        state_machine.validate_transition(WorkflowState.TRIAGED, WorkflowState.DECIDED)

def test_template_registry(template_registry):
    templates = template_registry.list_templates()
    assert len(templates) >= 4
    ato = template_registry.get_template("tmpl_ato_01")
    assert ato.workflow_type == WorkflowType.ACCOUNT_TAKEOVER
    assert len(ato.required_checks) >= 3
    assert len(ato.recommended_actions) >= 3
    
    with pytest.raises(TemplateNotFoundError):
        template_registry.get_template("invalid_template_id")
