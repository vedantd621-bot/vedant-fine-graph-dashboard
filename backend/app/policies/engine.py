"""
FinGraph Deterministic Policy Evaluation Engine.
Evaluates authorization requests against ordered tenant and system policies with default-deny semantics.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.policies.models import (
    Policy,
    PolicyCondition,
    PolicyEffect,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
)


class PolicyEngine:
    """
    Deterministic rule engine evaluating access permissions.
    Enforces strict tenant isolation and default-deny protection.
    """

    def evaluate(
        self,
        request: PolicyEvaluationRequest,
        policies: List[Policy],
    ) -> PolicyEvaluationResult:
        """
        Evaluates the request against active policies in ascending priority order.
        """
        now = datetime.now(timezone.utc)

        # 1. Platform Admin Bypass (scoped strictly to control-plane or authorized maintenance)
        if request.role == "PLATFORM_ADMIN":
            return PolicyEvaluationResult(
                effect=PolicyEffect.ALLOW,
                is_allowed=True,
                matched_policy_id="sys_platform_admin_override",
                reason="Platform Administrator authorized for platform governance.",
                evaluated_at=now,
            )

        # 2. Strict Cross-Tenant Guard: Deny immediately if tenant IDs do not match
        if request.tenant_id != request.resource_tenant_id:
            return PolicyEvaluationResult(
                effect=PolicyEffect.DENY,
                is_allowed=False,
                matched_policy_id="sys_cross_tenant_isolation_boundary",
                reason=f"Cross-tenant access forbidden: user tenant '{request.tenant_id}' does not match resource tenant '{request.resource_tenant_id}'.",
                evaluated_at=now,
            )

        # 3. Filter and sort active matching policies by priority (ascending)
        active_policies = [p for p in policies if p.enabled and (p.tenant_id == request.tenant_id or p.tenant_id == "GLOBAL")]
        active_policies.sort(key=lambda p: p.priority)

        for policy in active_policies:
            if not self._matches_resource(policy.resource, request.resource_type):
                continue
            if not self._matches_action(policy.action, request.action):
                continue
            if not self._matches_conditions(policy.conditions, request):
                continue

            # Matched rule
            is_allowed = (policy.effect == PolicyEffect.ALLOW)
            return PolicyEvaluationResult(
                effect=policy.effect,
                is_allowed=is_allowed,
                matched_policy_id=policy.policy_id,
                reason=f"Matched policy '{policy.name}' ({policy.policy_id}) with effect {policy.effect.value}.",
                evaluated_at=now,
            )

        # 4. Default Deny fallback
        return PolicyEvaluationResult(
            effect=PolicyEffect.DENY,
            is_allowed=False,
            matched_policy_id=None,
            reason=f"No matching ALLOW policy found for action '{request.action}' on resource '{request.resource_type}'. Default deny applied.",
            evaluated_at=now,
        )

    def _matches_resource(self, policy_resource: str, request_resource: str) -> bool:
        if policy_resource == "*" or policy_resource.lower() == "all":
            return True
        return policy_resource.lower() == request_resource.lower()

    def _matches_action(self, policy_action: str, request_action: str) -> bool:
        if policy_action == "*" or policy_action.lower() == "all":
            return True
        return policy_action.lower() == request_action.lower()

    def _matches_conditions(self, conditions: List[PolicyCondition], request: PolicyEvaluationRequest) -> bool:
        for cond in conditions:
            field = cond.field.lower()
            val = cond.value
            op = cond.operator.lower()

            req_val = None
            if field == "role":
                req_val = request.role
            elif field == "user_id":
                req_val = request.user_id
            elif field == "org_id":
                req_val = request.org_id
            elif field == "team_id":
                req_val = request.team_ids
            elif field in request.environment:
                req_val = request.environment[field]

            if op == "equals":
                if req_val != val:
                    return False
            elif op == "not_equals":
                if req_val == val:
                    return False
            elif op == "in":
                if isinstance(req_val, list):
                    if not any(v in val for v in req_val):
                        return False
                else:
                    if req_val not in val:
                        return False
            elif op == "not_in":
                if isinstance(req_val, list):
                    if any(v in val for v in req_val):
                        return False
                else:
                    if req_val in val:
                        return False
        return True
