# FinGraph Multi-Tenant Architecture & Data Isolation

---

## 1. Multi-Tenant Organizational Hierarchy

FinGraph models enterprise organizational structures using a strict 5-level domain hierarchy:

```text
[Tenant] (e.g. "Acme Corp Financials" - Root isolation boundary)
   │
   ├── [Organization] (e.g. "Acme EMEA Banking")
   │      │
   │      ├── [Business Unit] (e.g. "Retail Anti-Fraud Division")
   │      │      │
   │      │      └── [Investigation Team] (e.g. "High-Risk ATO Squad")
   │      │             │
   │      │             ├── [Team Member] (User: inv_alice, Role: LEAD)
   │      │             └── [Team Member] (User: inv_bob, Role: ANALYST)
   │      │
   │      └── [Business Unit] (e.g. "Corporate AML Division")
   │
   └── [Organization] (e.g. "Acme APAC Banking")
```

### Domain Entities & Attributes

* **Tenant**: Root entity containing `tenant_id`, `name`, `status` (`PENDING`, `ACTIVE`, `SUSPENDED`, `DISABLED`), `tier` (`COMMUNITY`, `STANDARD`, `ENTERPRISE`), `created_at`, `updated_at`.
* **Organization**: Regional or corporate subsidiary linked to a parent `tenant_id`.
* **Business Unit**: Functional division (e.g. AML, Fraud Operations, Compliance) linked to an `org_id` and `tenant_id`.
* **Investigation Team**: Operational team managing case queues and triage within a business unit.
* **Team Member**: Linkage between user and investigation team with assigned team roles (`LEAD`, `SENIOR`, `ANALYST`, `TRAINEE`).

---

## 2. Server-Side Tenant Context Injection

Every incoming request to the FinGraph API is scoped using the `TenantContext` dependency:

```python
class TenantContext(BaseModel):
    tenant_id: str
    org_id: Optional[str] = None
    unit_id: Optional[str] = None
    team_id: Optional[str] = None
    user_id: str
    username: str
    role: Role
    permissions: List[Permission] = Field(default_factory=list)
    is_platform_admin: bool = False
    attributes: Dict[str, Any] = Field(default_factory=dict)
```

### Resolution Order:
1. **Authentication Token**: The JWT payload supplies `user_id`, `role`, and assigned default `tenant_id`.
2. **Platform Admin Override**: Platform administrators can optionally target specific tenants via the `X-Tenant-ID` header.
3. **Tenant Status Verification**: Non-platform admin requests against `SUSPENDED` or `DISABLED` tenants are immediately rejected with `403 Forbidden` (`TenantSuspendedException` or `TenantDisabledException`).
4. **Tenant Isolation Enforcement**: Requests attempting to access resources belonging to a different tenant are blocked immediately.

---

## 3. Tenant Quotas & Resource Governance

Each tenant is configured with a deterministic `TenantQuota` and real-time usage telemetry:

| Quota Dimension | Standard Tier | Enterprise Tier | Exceeded Behavior |
| :--- | :---: | :---: | :--- |
| **Max Users** | 25 | Unlimited / Custom | Rejects user creation |
| **Max Concurrent Queries** | 50 | 500 | Returns HTTP 429 |
| **Max Daily Transactions** | 1,000,000 | 100,000,000 | Warns & throttles |
| **Max Custom Detectors** | 10 | 100 | Rejects new rule draft |
| **Storage Allocation (GB)** | 100 | 5,000 | Throttles history ingestion |

Usage metrics are tracked in `TenantUsageMetrics` and evaluated in sub-millisecond latency.
