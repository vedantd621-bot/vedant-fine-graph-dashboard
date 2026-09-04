# FinGraph Deterministic Policy Engine

---

## 1. Engine Architecture & Evaluation Semantics

The FinGraph Policy Engine enforces fine-grained, deterministic access control policies across all tenant operations.

```text
Request / Action Context
          │
          ▼
+─────────────────────────────────────────+
|      Deterministic Policy Evaluator     |
+─────────────────────────────────────────+
| 1. Cross-Tenant Check                   | -> If context.tenant != target.tenant & not PLATFORM_ADMIN
|                                         |    ==> Immediate DENY (Strict Boundary)
| 2. Policy Filtering                     | -> Filter active policies matching Tenant ID or GLOBAL
| 3. Rule Sorting                         | -> Order by priority ASC (lower number = higher precedence)
| 4. Condition Matching                   | -> Match role, user, time window, IP CIDR, resource attr
| 5. Evaluation & Decision Resolution     | -> ALLOW or DENY effect
| 6. Default Fallback                     | -> If no rule matches ==> Default DENY
+─────────────────────────────────────────+
          │
          ▼
  Policy Decision (ALLOWED / DENIED + Justification Trace)
```

---

## 2. Policy Definition & Rule Structure

Policies are structured as versioned documents with ordered rules:

```json
{
  "policy_id": "pol_freeze_protection_01",
  "tenant_id": "tnt_acme_corp",
  "name": "High-Value Account Freeze Protection",
  "status": "ACTIVE",
  "rules": [
    {
      "rule_id": "rule_deny_non_lead_freeze",
      "priority": 10,
      "effect": "DENY",
      "action": "action:freeze_account",
      "resource_pattern": "account:vip_*",
      "conditions": {
        "roles_not_in": ["ADMIN", "PLATFORM_ADMIN"],
        "min_case_priority": "P0_CRITICAL"
      },
      "description": "Deny freezing VIP accounts unless requested by Administrator"
    },
    {
      "rule_id": "rule_allow_investigator_freeze",
      "priority": 20,
      "effect": "ALLOW",
      "action": "action:freeze_account",
      "resource_pattern": "account:*",
      "conditions": {
        "roles_in": ["INVESTIGATOR", "ADMIN"]
      },
      "description": "Allow regular account freezing by Investigators"
    }
  ]
}
```

---

## 3. Condition Evaluation Operators

The deterministic policy engine supports pure, explainable condition evaluation without side effects:

* `roles_in` / `roles_not_in`: Checks whether subject's role belongs to the allowed list.
* `users_in`: Checks specific user identifiers.
* `ip_cidr_allow` / `ip_cidr_deny`: Matches client IP against CIDR subnets.
* `time_window`: Enforces business-hour or maintenance-window access constraints (UTC start/end hours).
* `resource_tags`: Matches metadata attributes attached to target resources.

---

## 4. Default-Deny & Auditable Explanations

* **Default-Deny**: In accordance with zero-trust principles, if no matching rule is found for an action on a resource, the engine returns `ALLOWED = False` with reason `Default Deny: No matching policy rule permitted this action`.
* **Audit Trail**: Every policy evaluation generates a complete trace detailing the matched policy ID, rule ID, evaluated condition results, and final decision for full audit compliance.
