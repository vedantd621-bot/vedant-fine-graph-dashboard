"""
Tests for Deterministic Policy Engine in Phase 20.
"""
import pytest
from backend.app.policies.engine import PolicyEngine
from backend.app.policies.models import (
    Policy,
    PolicyCondition,
    PolicyEffect,
    PolicyEvaluationRequest,
)

@pytest.fixture
def engine():
    return PolicyEngine()

def test_policy_allow_and_deny(engine):
    policies = [
        Policy(
            policy_id="p1",
            tenant_id="tnt_001",
            name="Allow Analyst Read",
            resource="case",
            action="read",
            conditions=[PolicyCondition(field="role", operator="equals", value="ANALYST")],
            effect=PolicyEffect.ALLOW,
            priority=100,
        ),
        Policy(
            policy_id="p2",
            tenant_id="tnt_001",
            name="Deny Delete",
            resource="case",
            action="delete",
            effect=PolicyEffect.DENY,
            priority=50,
        ),
    ]

    # 1. Allowed Read
    req_read = PolicyEvaluationRequest(
        user_id="usr_01",
        role="ANALYST",
        tenant_id="tnt_001",
        resource_type="case",
        resource_id="case_101",
        resource_tenant_id="tnt_001",
        action="read",
    )
    res_read = engine.evaluate(req_read, policies)
    assert res_read.is_allowed is True
    assert res_read.effect == PolicyEffect.ALLOW
    assert res_read.matched_policy_id == "p1"

    # 2. Denied Delete
    req_del = PolicyEvaluationRequest(
        user_id="usr_01",
        role="ANALYST",
        tenant_id="tnt_001",
        resource_type="case",
        resource_id="case_101",
        resource_tenant_id="tnt_001",
        action="delete",
    )
    res_del = engine.evaluate(req_del, policies)
    assert res_del.is_allowed is False
    assert res_del.effect == PolicyEffect.DENY

def test_cross_tenant_immediate_deny(engine):
    policies = [
        Policy(policy_id="p_all", tenant_id="tnt_001", name="Allow All", resource="*", action="*", effect=PolicyEffect.ALLOW)
    ]
    req_cross = PolicyEvaluationRequest(
        user_id="usr_01",
        role="ADMIN",
        tenant_id="tnt_001",
        resource_type="case",
        resource_id="case_999",
        resource_tenant_id="tnt_002",  # Different tenant!
        action="read",
    )
    res = engine.evaluate(req_cross, policies)
    assert res.is_allowed is False
    assert res.effect == PolicyEffect.DENY
    assert "Cross-tenant" in res.reason

def test_default_deny_when_no_match(engine):
    req_unmatched = PolicyEvaluationRequest(
        user_id="usr_01",
        role="GUEST",
        tenant_id="tnt_001",
        resource_type="secret_vault",
        resource_id="sec_01",
        resource_tenant_id="tnt_001",
        action="purge",
    )
    res = engine.evaluate(req_unmatched, [])
    assert res.is_allowed is False
    assert res.effect == PolicyEffect.DENY
    assert "Default deny" in res.reason
