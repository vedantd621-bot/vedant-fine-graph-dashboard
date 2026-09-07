"""
FinGraph Fraud Decisioning & Simulation Domain Models.
"""
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class DecisionVerdict(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    ESCALATE = "ESCALATE"
    BLOCK = "BLOCK"
    CONFIRM_FRAUD = "CONFIRM_FRAUD"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class DecisionConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FraudDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:12]}")
    alert_id: Optional[str] = None
    case_id: Optional[str] = None
    entity_id: Optional[str] = None
    tenant_id: str = "tnt_default"
    verdict: DecisionVerdict
    confidence: DecisionConfidence
    risk_score: float  # 0-100
    contributing_signals: List[str] = Field(default_factory=list)
    evidence_summary: str = ""
    recommendation: str = ""
    policy_version: Optional[str] = "v1.0"
    detector_versions: List[str] = Field(default_factory=list)
    created_by: str = "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_override: bool = False
    override_reference: Optional[str] = None


class DecisionOverride(BaseModel):
    override_id: str = Field(default_factory=lambda: f"ovr_{uuid.uuid4().hex[:12]}")
    decision_id: str
    tenant_id: str = "tnt_default"
    original_verdict: DecisionVerdict
    override_verdict: DecisionVerdict
    actor: str  # username
    reason: str
    evidence_references: List[str] = Field(default_factory=list)
    policy_context: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateDecisionRequest(BaseModel):
    alert_id: Optional[str] = None
    case_id: Optional[str] = None
    entity_id: Optional[str] = None
    risk_score: float = 50.0
    contributing_signals: List[str] = Field(default_factory=list)
    evidence_summary: str = ""
    policy_version: Optional[str] = "v1.0"
    detector_versions: List[str] = Field(default_factory=list)


class CreateOverrideRequest(BaseModel):
    override_verdict: DecisionVerdict
    reason: str
    evidence_references: List[str] = Field(default_factory=list)
    policy_context: Optional[str] = None


class SimulationParameter(BaseModel):
    name: str  # e.g. "risk_threshold", "detector_weight"
    current_value: Any
    hypothetical_value: Any
    description: str = ""


class SimulationRequest(BaseModel):
    scenario_name: str
    description: str = ""
    parameters: List[SimulationParameter] = Field(default_factory=list)
    alert_ids: List[str] = Field(default_factory=list)
    case_ids: List[str] = Field(default_factory=list)


class SimulationResult(BaseModel):
    simulation_id: str = Field(default_factory=lambda: f"sim_{uuid.uuid4().hex[:12]}")
    scenario_name: str
    description: str
    parameters: List[SimulationParameter]
    predicted_alerts_changed: int = 0
    predicted_risk_change: float = 0.0
    predicted_cases_impacted: int = 0
    predicted_exposure_change: float = 0.0
    recommendation_changes: List[str] = Field(default_factory=list)
    simulation_notes: str = ""
    is_production_safe: bool = True  # Always True - sandbox never mutates production data
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_by: str = "system"
