"""
FinGraph Policy Service.
Provides policy CRUD and evaluation integration with audit logging.
"""
from datetime import datetime, timezone
import json
from typing import Dict, List, Optional
import uuid

from backend.app.policies.engine import PolicyEngine
from backend.app.policies.exceptions import PolicyNotFoundError, PolicyValidationError
from backend.app.policies.models import (
    Policy,
    PolicyCondition,
    PolicyCreateRequest,
    PolicyEffect,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    PolicyUpdateRequest,
)
from backend.app.security.audit import AuditService, get_audit_service


class PolicyService:
    """Manages policy lifecycle and evaluations."""

    def __init__(self, audit_service: Optional[AuditService] = None):
        self._audit_service = audit_service or get_audit_service()
        self._engine = PolicyEngine()
        self._policies_by_id: Dict[str, Policy] = {}
        self._seed_default_policies()

    def _seed_default_policies(self) -> None:
        """Seeds built-in global and default-tenant policies."""
        defaults = [
            Policy(
                policy_id="pol_sys_analyst_read",
                tenant_id="GLOBAL",
                name="Analyst Platform Read Access",
                description="Allows Analysts to read alerts, cases, evidence, and dashboards",
                resource="*",
                action="read",
                conditions=[PolicyCondition(field="role", operator="in", value=["ANALYST", "INVESTIGATOR", "ADMIN", "PLATFORM_ADMIN"])],
                effect=PolicyEffect.ALLOW,
                priority=200,
            ),
            Policy(
                policy_id="pol_sys_investigator_crud",
                tenant_id="GLOBAL",
                name="Investigator Case & Evidence Management",
                description="Allows Investigators to create, update, and manage investigation cases and evidence",
                resource="case",
                action="*",
                conditions=[PolicyCondition(field="role", operator="in", value=["INVESTIGATOR", "ADMIN", "PLATFORM_ADMIN"])],
                effect=PolicyEffect.ALLOW,
                priority=150,
            ),
            Policy(
                policy_id="pol_sys_admin_full",
                tenant_id="GLOBAL",
                name="Tenant Administrator Full Access",
                description="Allows Tenant Admins full management within their tenant domain",
                resource="*",
                action="*",
                conditions=[PolicyCondition(field="role", operator="in", value=["ADMIN", "PLATFORM_ADMIN"])],
                effect=PolicyEffect.ALLOW,
                priority=100,
            ),
        ]
        for p in defaults:
            self._policies_by_id[p.policy_id] = p

    def create_policy(self, tenant_id: str, request: PolicyCreateRequest, actor_id: str) -> Policy:
        policy = Policy(
            tenant_id=tenant_id,
            name=request.name,
            description=request.description or "",
            resource=request.resource,
            action=request.action,
            conditions=request.conditions or [],
            effect=request.effect,
            priority=request.priority or 100,
            enabled=request.enabled if request.enabled is not None else True,
        )
        self._policies_by_id[policy.policy_id] = policy

        self._audit_service.record(
            user_id=actor_id,
            action="POLICY_CREATED",
            resource_type="POLICY",
            resource_id=policy.policy_id,
            new_value=json.dumps({"name": policy.name, "effect": policy.effect.value, "tenant_id": tenant_id}),
        )
        return policy

    def get_policy(self, policy_id: str) -> Policy:
        if policy_id not in self._policies_by_id:
            raise PolicyNotFoundError(f"Policy '{policy_id}' was not found.")
        return self._policies_by_id[policy_id]

    def list_policies(self, tenant_id: Optional[str] = None) -> List[Policy]:
        if tenant_id:
            return [p for p in self._policies_by_id.values() if p.tenant_id == tenant_id or p.tenant_id == "GLOBAL"]
        return list(self._policies_by_id.values())

    def update_policy(self, policy_id: str, request: PolicyUpdateRequest, actor_id: str) -> Policy:
        policy = self.get_policy(policy_id)
        old_val = json.dumps(policy.model_dump(mode="json"))

        if request.name is not None:
            policy.name = request.name
        if request.description is not None:
            policy.description = request.description
        if request.resource is not None:
            policy.resource = request.resource
        if request.action is not None:
            policy.action = request.action
        if request.conditions is not None:
            policy.conditions = request.conditions
        if request.effect is not None:
            policy.effect = request.effect
        if request.priority is not None:
            policy.priority = request.priority
        if request.enabled is not None:
            policy.enabled = request.enabled
        policy.updated_at = datetime.now(timezone.utc)

        self._audit_service.record(
            user_id=actor_id,
            action="POLICY_UPDATED",
            resource_type="POLICY",
            resource_id=policy_id,
            old_value=old_val,
            new_value=json.dumps(policy.model_dump(mode="json")),
        )
        return policy

    def delete_policy(self, policy_id: str, actor_id: str) -> bool:
        policy = self.get_policy(policy_id)
        del self._policies_by_id[policy_id]

        self._audit_service.record(
            user_id=actor_id,
            action="POLICY_DELETED",
            resource_type="POLICY",
            resource_id=policy_id,
            old_value=json.dumps({"name": policy.name, "tenant_id": policy.tenant_id}),
        )
        return True

    def evaluate_access(self, request: PolicyEvaluationRequest) -> PolicyEvaluationResult:
        """Evaluates policy access for a given request."""
        policies = list(self._policies_by_id.values())
        return self._engine.evaluate(request, policies)


# Singleton instance
_global_policy_service: Optional[PolicyService] = None


def get_policy_service() -> PolicyService:
    global _global_policy_service
    if _global_policy_service is None:
        _global_policy_service = PolicyService()
    return _global_policy_service
