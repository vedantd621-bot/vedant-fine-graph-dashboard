# FinGraph Enterprise Governance, Configuration Versioning & Role Matrix

---

## 1. Platform Administration vs. Investigation Boundary

FinGraph strictly separates **Platform Infrastructure Administration** from **Tenant Customer Investigation**:

* **`PLATFORM_ADMIN`**:
  * Manages global platform health, tenant provisioning, resource quotas, and baseline system policies.
  * Explicitly prohibited from unrestricted browsing of customer investigation dossiers, evidence vaults, and transaction histories without explicit scoped delegation.
* **`TENANT_ADMIN` (`ADMIN`)**:
  * Manages user onboarding, business units, investigation teams, and custom detection policies within their own tenant boundary.
* **`INVESTIGATOR`**:
  * Executes case investigations, triage, alert correlation, evidence attachment, and account freeze remediations.
* **`ANALYST`**:
  * Read-only inspection of graph neighborhoods, dashboards, timelines, and anomaly profiles within their assigned tenant.

---

## 2. Granular Permission Matrix (19 Permissions)

| Permission | Description | ANALYST | INVESTIGATOR | TENANT_ADMIN | PLATFORM_ADMIN |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `READ_GRAPH` | View accounts, graph nodes & paths | Yes | Yes | Yes | Yes |
| `SEARCH_ENTITIES` | Search cross-entity databases | Yes | Yes | Yes | Yes |
| `VIEW_ALERTS` | Inspect alert queues and queues | Yes | Yes | Yes | Yes |
| `VIEW_CASES` | View investigation dossiers | Yes | Yes | Yes | No (Boundary) |
| `VIEW_REPORTS` | Access operational analytics | Yes | Yes | Yes | Yes |
| `VIEW_METRICS` | View system metrics & SLAs | Yes | Yes | Yes | Yes |
| `TRIAGE_ALERTS` | Modify alert triage states | No | Yes | Yes | No |
| `ASSIGN_ALERTS` | Assign alerts to team members | No | Yes | Yes | No |
| `MUTATE_CASES` | Create, transition, close cases | No | Yes | Yes | No |
| `ATTACH_EVIDENCE` | Attach cryptographic evidence | No | Yes | Yes | No |
| `EXECUTE_DECISION` | Submit fraud decisioning verdicts | No | Yes | Yes | No |
| `FREEZE_ACCOUNT` | Trigger account freeze workflow | No | Yes | Yes | No |
| `MANAGE_USERS` | Create & modify tenant users | No | No | Yes | Yes (Global) |
| `MANAGE_TEAMS` | Manage investigation squads | No | No | Yes | Yes |
| `MANAGE_POLICIES` | Create/edit access policies | No | No | Yes | Yes (Global) |
| `MANAGE_CONFIG` | Deploy configuration versions | No | No | Yes | Yes |
| `VIEW_AUDIT_LOGS` | Access immutable audit trail | No | No | Yes | Yes |
| `MANAGE_TENANTS` | Create, suspend, delete tenants| No | No | No | Yes |
| `MANAGE_QUOTAS` | Modify tenant quota allocations | No | No | No | Yes |

---

## 3. Configuration Versioning Lifecycle

To prevent accidental outages or unreviewed rule changes, all tenant configuration changes follow an immutable lifecycle:

```text
  [ Create Draft ]
         │
         ▼
     [ DRAFT ] ──────────► [ ACTIVE ] ──────────► [ RETIRED ]
         │                     │
         ▼                     ▼
     [ ARCHIVED ]         [ Rollback ]
```

* **DRAFT**: Editable configuration draft containing threshold overrides, detector weights, and feature toggles.
* **ACTIVE**: Exactly one active configuration version per tenant at any time. Immutable once activated.
* **RETIRED**: Superseded configuration retained permanently for audit and historical investigation reproducibility.
* **Rollback**: Instant rollback activates a previously retired version without mutating historical records.
