"""
Decisioning & Simulation REST Endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.decisioning.exceptions import DecisionNotFoundException
from backend.app.decisioning.models import (
    CreateDecisionRequest, CreateOverrideRequest, DecisionOverride,
    DecisionVerdict, FraudDecision, SimulationRequest, SimulationResult
)
from backend.app.decisioning.service import DecisionService, get_decisioning_service
from backend.app.security.audit import get_audit_service
from backend.app.security.dependencies import (
    get_current_user, require_admin, require_analyst, require_investigator
)
from backend.app.security.models import User

router = APIRouter(prefix="/api/v1/decisioning", tags=["decisioning"])


@router.get("/verdicts", response_model=List[str])
def list_verdicts(current_user: User = Depends(require_analyst)):
    """List supported deterministic decision verdicts."""
    return [v.value for v in DecisionVerdict]


@router.get("/summary")
def get_decisioning_summary(
    current_user: User = Depends(require_analyst),
    service: DecisionService = Depends(get_decisioning_service),
):
    """Summarizes decisions count and verdict distribution."""
    decisions = service.list_decisions(current_user.tenant_id, limit=500)
    distribution = {}
    for d in decisions:
        distribution[d.verdict.value] = distribution.get(d.verdict.value, 0) + 1
    return {
        "tenant_id": current_user.tenant_id,
        "total_decisions": len(decisions),
        "verdict_distribution": distribution,
        "overrides_count": sum(1 for d in decisions if d.is_override),
    }


@router.post("/simulate", response_model=SimulationResult)
def run_simulation(
    req: SimulationRequest,
    current_user: User = Depends(require_investigator),
    service: DecisionService = Depends(get_decisioning_service),
    audit = Depends(get_audit_service),
):
    """Run an isolated What-If simulation scenario without mutating production state."""
    res = service.run_simulation(req, current_user.tenant_id, current_user.username)
    audit.record(
        user_id=current_user.user_id,
        action="DECISIONING_SIMULATION_RUN",
        resource_type="SIMULATION",
        resource_id=res.simulation_id,
        tenant_id=current_user.tenant_id,
        new_value=req.scenario_name,
    )
    return res


@router.get("/", response_model=List[FraudDecision])
def list_decisions(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_analyst),
    service: DecisionService = Depends(get_decisioning_service),
):
    """List fraud decisions for the authenticated tenant."""
    return service.list_decisions(current_user.tenant_id, limit=limit)


@router.post("/", response_model=FraudDecision, status_code=status.HTTP_201_CREATED)
def create_decision(
    req: CreateDecisionRequest,
    current_user: User = Depends(require_investigator),
    service: DecisionService = Depends(get_decisioning_service),
    audit = Depends(get_audit_service),
):
    """Generate a deterministic fraud decision based on risk and evidence."""
    decision = service.create_decision(req, current_user.tenant_id, current_user.username)
    audit.record(
        user_id=current_user.user_id,
        action="DECISION_CREATED",
        resource_type="DECISION",
        resource_id=decision.decision_id,
        tenant_id=current_user.tenant_id,
        new_value=decision.verdict.value,
    )
    return decision


@router.get("/{decision_id}", response_model=FraudDecision)
def get_decision(
    decision_id: str,
    current_user: User = Depends(require_analyst),
    service: DecisionService = Depends(get_decisioning_service),
):
    """Get decision details by ID."""
    try:
        return service.get_decision(decision_id, current_user.tenant_id)
    except DecisionNotFoundException:
        raise HTTPException(status_code=404, detail=f"Decision '{decision_id}' not found.")


@router.post("/{decision_id}/override", response_model=DecisionOverride)
def create_override(
    decision_id: str,
    req: CreateOverrideRequest,
    current_user: User = Depends(require_admin),
    service: DecisionService = Depends(get_decisioning_service),
    audit = Depends(get_audit_service),
):
    """Authorized human-in-the-loop override of a deterministic decision."""
    try:
        ovr = service.create_override(decision_id, req, current_user.tenant_id, current_user.username)
        audit.record(
            user_id=current_user.user_id,
            action="DECISION_OVERRIDDEN",
            resource_type="DECISION",
            resource_id=decision_id,
            tenant_id=current_user.tenant_id,
            old_value=ovr.original_verdict.value,
            new_value=ovr.override_verdict.value,
        )
        return ovr
    except DecisionNotFoundException:
        raise HTTPException(status_code=404, detail=f"Decision '{decision_id}' not found.")


@router.get("/{decision_id}/overrides", response_model=List[DecisionOverride])
def get_overrides(
    decision_id: str,
    current_user: User = Depends(require_analyst),
    service: DecisionService = Depends(get_decisioning_service),
):
    """List immutable override history for a decision."""
    try:
        return service.get_overrides(decision_id, current_user.tenant_id)
    except DecisionNotFoundException:
        raise HTTPException(status_code=404, detail=f"Decision '{decision_id}' not found.")
