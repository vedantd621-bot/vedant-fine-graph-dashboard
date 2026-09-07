# FinGraph Master Enterprise Security & RBAC Matrix

---

## 1. Enterprise Personas & Role Hierarchy

| Persona | Role Enum | Scope | Description |
| :--- | :--- | :--- | :--- |
| **Platform Administrator** | `PLATFORM_ADMIN` | Global | Manages platform health, tenant lifecycle, quotas, and global policies. Restricted from viewing raw customer case evidence without explicit delegation. |
| **Tenant Administrator** | `ADMIN` / `TENANT_ADMIN`| Tenant | Full administrative authority within tenant scope: user onboarding, team creation, policy governance, and report scheduling. |
| **Lead Investigator** | `INVESTIGATOR` | Tenant | Triage alerts, mutate cases, attach cryptographic evidence, create fraud decisions, and execute What-If simulations. |
| **Reviewer** | `REVIEWER` | Tenant | Perform second-line review of investigations, inspect evidence, and evaluate decision overrides. |
| **Auditor** | `AUDITOR` | Tenant | Inspect immutable audit trails, review historical snapshots, verify cryptographic digests, and monitor compliance. |
| **Executive** | `EXECUTIVE` | Tenant | High-level executive posture monitoring, KPI exploration, report generation, and CSV/JSON data export. |
| **Analyst** | `ANALYST` | Tenant | Read-only inspection of graph neighborhoods, alert queues, dashboards, and network dossiers. |
| **Read Only** | `READ_ONLY` | Tenant | Minimal read-only viewer for external stakeholders. |

---

## 2. Granular Permissions Mapping (31 Permissions)

| Permission | ANALYST | INVESTIGATOR | REVIEWER | AUDITOR | EXECUTIVE | TENANT_ADMIN | PLATFORM_ADMIN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `ALERT_READ` | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `ALERT_UPDATE` | No | Yes | No | No | No | Yes | Yes |
| `CASE_READ` | Yes | Yes | Yes | Yes | Yes | Yes | Boundary |
| `CASE_CREATE` | No | Yes | No | No | No | Yes | No |
| `CASE_UPDATE` | No | Yes | No | No | No | Yes | No |
| `CASE_ASSIGN` | No | Yes | No | No | No | Yes | No |
| `CASE_CLOSE` | No | Yes | No | No | No | Yes | No |
| `EVIDENCE_READ` | Yes | Yes | Yes | Yes | No | Yes | No |
| `EVIDENCE_CREATE` | No | Yes | No | No | No | Yes | No |
| `DECISION_READ` | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `DECISION_CREATE` | No | Yes | No | No | No | Yes | No |
| `DECISION_OVERRIDE`| No | No | Yes | No | No | Yes | No |
| `SIMULATION_RUN` | No | Yes | No | No | No | Yes | Yes |
| `ANALYTICS_READ` | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `REPORT_READ` | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `REPORT_CREATE` | Yes | Yes | Yes | No | Yes | Yes | Yes |
| `REPORT_EXPORT` | No | No | No | No | Yes | Yes | Yes |
| `AUDIT_READ` | No | No | No | Yes | No | Yes | Yes |
| `TENANT_READ` | No | No | No | No | No | Yes | Yes |
| `TENANT_WRITE` | No | No | No | No | No | Yes | Yes |
| `USER_READ` | No | No | No | No | No | Yes | Yes |
| `USER_WRITE` | No | No | No | No | No | Yes | Yes |
| `TEAM_READ` | No | No | No | No | No | Yes | Yes |
| `TEAM_WRITE` | No | No | No | No | No | Yes | Yes |
