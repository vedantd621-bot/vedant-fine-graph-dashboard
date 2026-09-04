# Alert Prioritization & Triage Lifecycle Guide

## 1. Prioritization Mathematical Formulation

FinGraph evaluates every fraud detection alert using a deterministic, 4-factor weighted scoring model ($0 - 100$):

$$\text{PriorityScore} = 30 \cdot \text{EntityRisk} + 25 \cdot \text{NetworkRisk} + 25 \cdot \text{SeverityImpact} + 20 \cdot \text{AnomalyVelocity}$$

### Contributing Factors:
- **Entity Graph Risk** ($w = 0.30$): Primary account composite risk score ($0–100$) from the explainable graph risk engine.
- **Syndicate Network Risk** ($w = 0.25$): Aggregate community/syndicate risk score if the entity participates in a discovered fraud ring.
- **Severity & Financial Impact** ($w = 0.25$): Rule severity weight (`CRITICAL`=100, `HIGH`=75, `MEDIUM`=50, `LOW`=25) combined with normalized exposure magnitude.
- **Behavioral Anomaly & Velocity** ($w = 0.20$): Active temporal deviations and count of co-occurring alerts on the focal account.

### Priority Tiers:
- **`P0_CRITICAL`** ($\ge 80.0$): Immediate threat requiring response within 15 minutes.
- **`P1_HIGH`** ($60.0 - 79.9$): Elevated threat with 1 hour SLA.
- **`P2_MEDIUM`** ($35.0 - 59.9$): Standard review with 4 hour SLA.
- **`P3_LOW`** ($< 35.0$): Routine backlog with 24 hour SLA.

---

## 2. 7-State Triage State Machine

```
   [NEW]
     │
     ├───────────────┬────────────────┬──────────────┐
     ▼               ▼                ▼              ▼
 [TRIAGED] ──► [INVESTIGATING] ──► [FALSE_POSITIVE] [CLOSED]
     │               │                │              ▲
     │               ├──────────────┐ │              │
     │               ▼              ▼ ▼              │
     └───────► [ESCALATED] ──► [CONFIRMED_FRAUD] ────┘
```

### Valid State Transitions:
1. `NEW` $	o$ `TRIAGED`, `INVESTIGATING`, `FALSE_POSITIVE`, `CLOSED`
2. `TRIAGED` $	o$ `INVESTIGATING`, `ESCALATED`, `FALSE_POSITIVE`, `CLOSED`
3. `INVESTIGATING` $	o$ `ESCALATED`, `CONFIRMED_FRAUD`, `FALSE_POSITIVE`, `CLOSED`
4. `ESCALATED` $	o$ `CONFIRMED_FRAUD`, `FALSE_POSITIVE`, `CLOSED`
5. `CONFIRMED_FRAUD` $	o$ `CLOSED`
6. `FALSE_POSITIVE` $	o$ `CLOSED`
7. `CLOSED` $	o$ `NEW` (Re-opened by authorized investigator/admin)

---

## 3. RBAC & Audit Trail Logging

- **`ANALYST`**: Read-only access to queues and priority explanations.
- **`INVESTIGATOR` & `ADMIN`**: Permitted to transition triage states, assign/reassign alerts, and perform bulk actions.
- Every state change logs an immutable `AuditLog` entry recording `user_id`, `username`, `old_value`, `new_value`, `timestamp`, and `request_id`.
