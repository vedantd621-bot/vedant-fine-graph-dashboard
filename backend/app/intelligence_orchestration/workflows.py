"""
FinGraph Investigation Workflow Templates & Lifecycle State Machine.
Defines standardized workflow templates and validates legal state transitions.
"""
from typing import Dict, List, Optional

from backend.app.intelligence_orchestration.exceptions import (
    InvalidWorkflowTransitionError,
    TemplateNotFoundError,
)
from backend.app.intelligence_orchestration.models import (
    InvestigationWorkflowTemplate,
    WorkflowState,
    WorkflowType,
)


class WorkflowStateMachine:
    """
    Validates and enforces legal lifecycle state transitions for investigation cases.
    CREATED -> TRIAGED -> INVESTIGATING -> EVIDENCE_REVIEW -> DECISION_PENDING -> DECIDED -> CLOSED
    """

    LEGAL_TRANSITIONS = {
        WorkflowState.CREATED: [WorkflowState.TRIAGED, WorkflowState.CLOSED],
        WorkflowState.TRIAGED: [WorkflowState.INVESTIGATING, WorkflowState.CLOSED],
        WorkflowState.INVESTIGATING: [WorkflowState.EVIDENCE_REVIEW, WorkflowState.DECISION_PENDING, WorkflowState.CLOSED],
        WorkflowState.EVIDENCE_REVIEW: [WorkflowState.DECISION_PENDING, WorkflowState.INVESTIGATING, WorkflowState.CLOSED],
        WorkflowState.DECISION_PENDING: [WorkflowState.DECIDED, WorkflowState.INVESTIGATING, WorkflowState.CLOSED],
        WorkflowState.DECIDED: [WorkflowState.CLOSED, WorkflowState.INVESTIGATING],
        WorkflowState.CLOSED: [WorkflowState.INVESTIGATING],  # Reopening
    }

    def validate_transition(self, current_state: WorkflowState, target_state: WorkflowState) -> None:
        """Raises InvalidWorkflowTransitionError if transition is illegal."""
        allowed = self.LEGAL_TRANSITIONS.get(current_state, [])
        if target_state not in allowed:
            raise InvalidWorkflowTransitionError(
                f"Cannot transition case from '{current_state.value}' to '{target_state.value}'. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )


class WorkflowTemplateRegistry:
    """
    Repository of standardized procedural investigation workflow templates.
    """

    def __init__(self):
        self._templates: Dict[str, InvestigationWorkflowTemplate] = {}
        self._seed_templates()

    def _seed_templates(self) -> None:
        templates = [
            InvestigationWorkflowTemplate(
                template_id="tmpl_ato_01",
                name="Account Takeover (ATO) Investigation Workflow",
                workflow_type=WorkflowType.ACCOUNT_TAKEOVER,
                trigger_conditions=["Simultaneous IP logins", "Device fingerprint mismatch", "Immediate password change + outbound wire"],
                required_checks=["Validate device fingerprint history", "Review 2FA authentication logs", "Confirm contact info update timestamp"],
                recommended_evidence=["Device telemetry", "IP geolocation logs", "Transaction velocity"],
                recommended_actions=["Temporary credential lock", "Quarantine outbound transfers", "Notify account holder"],
                completion_conditions=["Customer confirmation received", "Credentials rotated", "Fraudulent wire recalled"],
            ),
            InvestigationWorkflowTemplate(
                template_id="tmpl_mule_02",
                name="Money Mule / Rapid Layering Network Workflow",
                workflow_type=WorkflowType.MONEY_MULE,
                trigger_conditions=["High-velocity in-and-out transfers", "Zero balance retention", "Multiple distinct remitters"],
                required_checks=["Analyze 2-hop counterparty graph", "Check SAR/STR filing history", "Review beneficiary account age"],
                recommended_evidence=["Sub-graph evidence tree", "Counterparty risk profiles", "Layering velocity delta"],
                recommended_actions=["Place debit hold on mule node", "File regulatory suspicious activity report", "Quarantine exit bridges"],
                completion_conditions=["All outbound nodes reviewed", "Regulatory report drafted", "Case linked to syndicate campaign"],
            ),
            InvestigationWorkflowTemplate(
                template_id="tmpl_payment_03",
                name="Card & Payment Fraud Investigation Workflow",
                workflow_type=WorkflowType.PAYMENT_FRAUD,
                trigger_conditions=["Multiple card testing charges", "Rapid authorization velocity", "High chargeback ratio"],
                required_checks=["Inspect merchant category codes", "Review BIN routing", "Verify 3DS verification status"],
                recommended_evidence=["Authorization logs", "Terminal IDs", "Merchant chargeback telemetry"],
                recommended_actions=["Block compromised PAN", "Update merchant risk tier", "Issue chargeback dispute"],
                completion_conditions=["Card blocked", "Chargebacks processed", "Merchant notified"],
            ),
            InvestigationWorkflowTemplate(
                template_id="tmpl_syndicate_04",
                name="Coordinated Fraud Syndicate Investigation Workflow",
                workflow_type=WorkflowType.NETWORK_FRAUD,
                trigger_conditions=["Dense multi-entity cluster", "Shared proxy infrastructure", "Multi-account structuring"],
                required_checks=["Execute multi-hop threat propagation", "Identify campaign correlations", "Assess aggregate exposure"],
                recommended_evidence=["Graph topology", "Shared hardware hashes", "Campaign correlation matrix"],
                recommended_actions=["Network-level freeze", "Escalate to Senior Fraud Ops", "Deploy adaptive detector version"],
                completion_conditions=["All cluster nodes quarantined", "Executive brief approved", "Syndicate campaign confirmed"],
            ),
        ]
        for t in templates:
            self._templates[t.template_id] = t

    def list_templates(self) -> List[InvestigationWorkflowTemplate]:
        return list(self._templates.values())

    def get_template(self, template_id: str) -> InvestigationWorkflowTemplate:
        if template_id not in self._templates:
            raise TemplateNotFoundError(f"Workflow template '{template_id}' was not found.")
        return self._templates[template_id]
