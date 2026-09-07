"""
Decisioning Service & What-If Simulation Sandbox.
"""
import threading
from typing import Dict, List, Optional
from backend.app.decisioning.models import (
    CreateDecisionRequest, CreateOverrideRequest, DecisionConfidence,
    DecisionOverride, DecisionVerdict, FraudDecision, SimulationRequest, SimulationResult
)
from backend.app.decisioning.exceptions import DecisionNotFoundException


class DecisionService:
    """Thread-safe fraud decisioning repository and simulation engine."""

    def __init__(self):
        self._decisions: Dict[str, FraudDecision] = {}
        self._overrides: Dict[str, List[DecisionOverride]] = {}
        self._lock = threading.RLock()
        self._seed_sample_decisions()

    def _seed_sample_decisions(self):
        sample = [
            ("alt_001", "cas_001", "acc_101", 92.5, ["CircularFlow", "HighDegree"], DecisionVerdict.BLOCK, DecisionConfidence.HIGH),
            ("alt_002", "cas_002", "acc_102", 74.0, ["FunnelDetector"], DecisionVerdict.ESCALATE, DecisionConfidence.MEDIUM),
            ("alt_003", None, "acc_103", 56.0, ["VelocityAnomaly"], DecisionVerdict.REVIEW, DecisionConfidence.MEDIUM),
            ("alt_004", None, "acc_104", 22.0, [], DecisionVerdict.ALLOW, DecisionConfidence.LOW),
        ]
        for aid, cid, eid, risk, sigs, verd, conf in sample:
            d = FraudDecision(
                alert_id=aid,
                case_id=cid,
                entity_id=eid,
                tenant_id="tnt_default",
                verdict=verd,
                confidence=conf,
                risk_score=risk,
                contributing_signals=sigs,
                evidence_summary=f"Automated risk scoring based on {len(sigs)} active topological detector signals.",
                recommendation="Review required" if risk >= 50 else "Monitor",
            )
            self._decisions[d.decision_id] = d

    def _determine_verdict(self, risk_score: float) -> DecisionVerdict:
        if risk_score >= 85.0:
            return DecisionVerdict.BLOCK
        elif risk_score >= 70.0:
            return DecisionVerdict.ESCALATE
        elif risk_score >= 50.0:
            return DecisionVerdict.REVIEW
        else:
            return DecisionVerdict.ALLOW

    def _determine_confidence(self, signals: list) -> DecisionConfidence:
        if len(signals) >= 3:
            return DecisionConfidence.HIGH
        elif len(signals) >= 1:
            return DecisionConfidence.MEDIUM
        return DecisionConfidence.LOW

    def create_decision(self, req: CreateDecisionRequest, tenant_id: str, created_by: str) -> FraudDecision:
        verdict = self._determine_verdict(req.risk_score)
        confidence = self._determine_confidence(req.contributing_signals)
        
        if verdict == DecisionVerdict.BLOCK:
            recommendation = "Immediately block this entity and freeze funds. Escalate to Lead Investigator."
        elif verdict == DecisionVerdict.ESCALATE:
            recommendation = "Escalate to Tier-2 Fraud Squad for expedited review within SLA window."
        elif verdict == DecisionVerdict.REVIEW:
            recommendation = "Assign to available investigator for triage."
        else:
            recommendation = "No immediate remediation needed. Continue normal telemetry monitoring."

        decision = FraudDecision(
            alert_id=req.alert_id,
            case_id=req.case_id,
            entity_id=req.entity_id,
            tenant_id=tenant_id,
            verdict=verdict,
            confidence=confidence,
            risk_score=req.risk_score,
            contributing_signals=req.contributing_signals,
            evidence_summary=req.evidence_summary or f"Evaluated with risk score {req.risk_score}.",
            recommendation=recommendation,
            policy_version=req.policy_version or "v1.0",
            detector_versions=req.detector_versions or ["v1.0"],
            created_by=created_by,
        )
        with self._lock:
            self._decisions[decision.decision_id] = decision
        return decision

    def get_decision(self, decision_id: str, tenant_id: str) -> FraudDecision:
        with self._lock:
            d = self._decisions.get(decision_id)
            if not d:
                raise DecisionNotFoundException(decision_id)
            if tenant_id != "GLOBAL" and d.tenant_id != tenant_id:
                raise DecisionNotFoundException(decision_id)
            return d

    def list_decisions(self, tenant_id: str, limit: int = 100) -> List[FraudDecision]:
        with self._lock:
            if tenant_id == "GLOBAL":
                results = list(self._decisions.values())
            else:
                results = [d for d in self._decisions.values() if d.tenant_id == tenant_id]
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]

    def create_override(self, decision_id: str, req: CreateOverrideRequest, tenant_id: str, actor: str) -> DecisionOverride:
        decision = self.get_decision(decision_id, tenant_id)
        override = DecisionOverride(
            decision_id=decision_id,
            tenant_id=decision.tenant_id,
            original_verdict=decision.verdict,
            override_verdict=req.override_verdict,
            actor=actor,
            reason=req.reason,
            evidence_references=req.evidence_references,
            policy_context=req.policy_context,
        )
        with self._lock:
            if decision_id not in self._overrides:
                self._overrides[decision_id] = []
            self._overrides[decision_id].append(override)
            decision.is_override = True
            decision.override_reference = override.override_id
            decision.verdict = req.override_verdict
        return override

    def get_overrides(self, decision_id: str, tenant_id: str) -> List[DecisionOverride]:
        self.get_decision(decision_id, tenant_id)
        with self._lock:
            return list(self._overrides.get(decision_id, []))

    def run_simulation(self, req: SimulationRequest, tenant_id: str, executed_by: str) -> SimulationResult:
        # PURE SANDBOX: Evaluates hypothetical effects without touching production state
        total_risk_change = 0.0
        alerts_changed = 0
        notes = []

        for p in req.parameters:
            try:
                curr = float(p.current_value)
                hypo = float(p.hypothetical_value)
                delta = hypo - curr
                total_risk_change += delta
                if abs(delta) > 5.0:
                    alerts_changed += max(1, len(req.alert_ids))
                notes.append(f"Param '{p.name}': {curr} -> {hypo} (delta: {delta:+.2f})")
            except (ValueError, TypeError):
                notes.append(f"Param '{p.name}': {p.current_value} -> {p.hypothetical_value}")

        cases_impacted = max(1, len(req.case_ids)) if req.case_ids else (alerts_changed // 2)
        exposure_change = total_risk_change * 750.0

        recs = []
        if total_risk_change > 10.0:
            recs.append("Higher risk weighting will increase alert triage volume by estimated 15-25%.")
        elif total_risk_change < -10.0:
            recs.append("Relaxed thresholds reduce alerts but may increase undetected leakage.")
        else:
            recs.append("Moderate parameter variation maintains SLA stability within +/- 5% delta.")

        return SimulationResult(
            scenario_name=req.scenario_name,
            description=req.description,
            parameters=req.parameters,
            predicted_alerts_changed=alerts_changed,
            predicted_risk_change=round(total_risk_change, 2),
            predicted_cases_impacted=cases_impacted,
            predicted_exposure_change=round(exposure_change, 2),
            recommendation_changes=recs,
            simulation_notes="; ".join(notes),
            is_production_safe=True,
            executed_by=executed_by,
        )


_decisioning_service: Optional[DecisionService] = None


def get_decisioning_service() -> DecisionService:
    global _decisioning_service
    if _decisioning_service is None:
        _decisioning_service = DecisionService()
    return _decisioning_service
