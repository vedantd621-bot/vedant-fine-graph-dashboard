# FinGraph Phase 19: Enterprise-Scale Fraud Intelligence, Investigation Automation & Intelligence Orchestration

---

## 1. Overview & Objectives

**FinGraph Phase 19** introduces an **Intelligence Orchestration & Investigation Automation Layer** that coordinates all fraud detection, risk scoring, network evolution, case intelligence, decisioning, early warnings, threat propagation, and adaptive recommendations without duplicating algorithms or introducing unsupervised black-box decisions.

The orchestration layer provides:
1. **Central Intelligence Orchestrator**: Unified facade accessing all platform intelligence engines.
2. **Cross-Alert Multi-Signal Correlation**: Deterministic linking of alerts via shared accounts, devices, counterparties, IPs, and temporal proximity.
3. **Deterministic Investigation Priority Engine**: 6-factor composite priority score ($0–100$) and discrete priority bands (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
4. **Forensic Evidence Ranking & Provenance**: Deterministic ranking into `STRONG`, `MODERATE`, `WEAK`, and `INCONCLUSIVE` tiers with full source traceability.
5. **Automated Investigation Brief Generator**: Synthesizes executive dossiers, financial exposure, risk profiles, timelines, open questions, and transparent "NOT AVAILABLE" fallbacks.
6. **Standardized Workflow Templates & Lifecycle State Machine**: Enforces legal state progression (`CREATED` -> `TRIAGED` -> `INVESTIGATING` -> `EVIDENCE_REVIEW` -> `DECISION_PENDING` -> `DECIDED` -> `CLOSED`) and reopening workflows.
7. **Investigation Task & Checklist Management**: Granular task assignments, status tracking, and interactive case checklists with audit logs.
8. **Unified Forensic Intelligence Timeline**: Chronological event stream aggregating transactions, alerts, warnings, tasks, comments, evidence, and threat propagation.
9. **Related-Case Discovery Engine**: Identifies connected historical/concurrent cases based on shared hardware, proxy subnets, and syndicate campaigns.
10. **Advisory Investigation Recommendations**: Actionable next-step proposals without automated case closures.
11. **REST APIs & WebSocket Broadcasts**: 22 dedicated endpoints mounted under `/api/v1/orchestration/*` and 8 typed real-time events.
12. **Frontend Investigation Workstations**: `InvestigationIntelligencePage.tsx`, `AlertCorrelationPage.tsx`, and `TaskManagementPage.tsx`.

---

## 2. Architecture & Pipeline

```text
Transactions / Ingestion
        ↓
Stream CEP (Kafka / Flink)
        ↓
Graph Store (Neo4j / GDS)
        ↓
Detection & Risk Engines
        ↓
Intelligence Layer (Networks, Evolution, Early Warning, Propagation)
        ↓
========================================================================
       PHASE 19 INTELLIGENCE ORCHESTRATION & INVESTIGATION AUTOMATION
========================================================================
  [Cross-Alert Correlation]    [Priority Engine]    [Evidence Ranking]
              │                        │                    │
              └───────────────┬────────┘                    │
                              ↓                             │
                 [Automated Brief Synthesizer] ◄────────────┘
                              │
  [Workflow State Machine] ◄──┼──► [Task & Checklist Manager]
                              │
  [Unified Forensic Timeline] ◄──┼──► [Related-Case Discovery]
                              │
                 [Advisory Recommendations]
========================================================================
        ↓
REST APIs (/api/v1/orchestration/*) + WebSocket Events
        ↓
Frontend Workstations (Investigation, Correlation, Task Management)
```

---

## 3. Mathematical Formulations & Deterministic Rules

### 3.1 Investigation Priority Score ($0–100$)

$$\\text{PriorityScore} = w_{\\text{risk}} R + w_{\\text{exp}} E + w_{\\text{sev}} S + w_{\\text{sla}} L + w_{\\text{prop}} P + w_{\\text{camp}} C$$

Where:
* $w_{\\text{risk}} = 0.25$: Entity risk score index ($0–100$).
* $w_{\\text{exp}} = 0.20$: Financial exposure index, scaled relative to $150,000 threshold:
  $$E = \\min\\left(100.0, \\frac{\\text{Exposure}}{150000} \\times 100.0\\right)$$
* $w_{\\text{sev}} = 0.15$: Alert severity score (`CRITICAL` = 100, `HIGH` = 75, `MEDIUM` = 50, `LOW` = 25).
* $w_{\\text{sla}} = 0.15$: SLA triage urgency factor:
  $$L = \\min\\left(100.0, \\max\\left(0.0, \\frac{24.0 - \\text{SLA}_{\\text{hours}}}{24.0} \\times 100.0\\right)\\right)$$
* $w_{\\text{prop}} = 0.15$: Multi-hop contagion spread score ($0–100$).
* $w_{\\text{camp}} = 0.10$: Coordinated campaign linkage (100 if active campaign present, else 0).

**Priority Bands**:
* **`CRITICAL`**: $\\text{PriorityScore} \\ge 80.0$
* **`HIGH`**: $60.0 \\le \\text{PriorityScore} < 80.0$
* **`MEDIUM`**: $35.0 \\le \\text{PriorityScore} < 60.0$
* **`LOW`**: $\\text{PriorityScore} < 35.0$

### 3.2 Evidence Strength Classification Tiers

| Tier | Minimum Confidence | Sources & Provenance Criteria |
| :--- | :---: | :--- |
| **STRONG** | $\\ge 0.90$ | Verified multi-node graph cycles, direct hardware canvas/hash collisions, cryptographically verified evidence |
| **MODERATE** | $\\ge 0.75$ | Velocity anomalies ($>3\\sigma$), confirmed campaign proxy linkages, behavioral drift |
| **WEAK** | $\\ge 0.50$ | Single IP geolocation discrepancies, unconfirmed third-party telemetry |
| **INCONCLUSIVE** | $< 0.50$ | Missing attributes, ambiguous or corrupted log artifacts |

---

## 4. Lifecycle State Machine

Legal transitions are strictly validated:

```text
[CREATED] ──► [TRIAGED] ──► [INVESTIGATING] ──► [EVIDENCE_REVIEW] ──► [DECISION_PENDING] ──► [DECIDED] ──► [CLOSED]
    │             │                 ▲                                                             │
    │             │                 │                                                             │
    └─────────────┴─────────────────┴───────────── (Reopen Case) ◄────────────────────────────────┘
```

---

## 5. REST API Inventory

All routes are secured by JWT Bearer Authentication and RBAC roles:

| Method | Route | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/orchestration/correlations/{alert_id}` | Analyst+ | Get explainable multi-signal correlation for an alert |
| `POST` | `/api/v1/orchestration/correlations/correlate` | Investigator+ | Execute on-demand alert correlation analysis |
| `POST` | `/api/v1/orchestration/priority/calculate` | Analyst+ | Calculate deterministic investigation priority score |
| `GET` | `/api/v1/orchestration/evidence/{case_id}` | Analyst+ | Retrieve ranked forensic evidence with provenance |
| `GET` | `/api/v1/orchestration/brief/{case_or_alert_id}` | Analyst+ | Get synthesized investigation brief |
| `POST` | `/api/v1/orchestration/brief/generate` | Investigator+ | Force refresh / regenerate investigation brief |
| `GET` | `/api/v1/orchestration/templates` | Analyst+ | List standardized investigation workflow templates |
| `GET` | `/api/v1/orchestration/templates/{template_id}` | Analyst+ | Get workflow template details |
| `GET` | `/api/v1/orchestration/cases/{case_id}/workflow-state` | Analyst+ | Get current case workflow state |
| `POST` | `/api/v1/orchestration/cases/{case_id}/workflow-state` | Investigator+ | Transition case workflow state |
| `GET` | `/api/v1/orchestration/tasks` | Analyst+ | List investigation tasks with filters |
| `POST` | `/api/v1/orchestration/tasks` | Investigator+ | Create investigation task |
| `GET` | `/api/v1/orchestration/tasks/{task_id}` | Analyst+ | Get investigation task details |
| `PUT` | `/api/v1/orchestration/tasks/{task_id}` | Investigator+ | Update task status, priority, or assignee |
| `POST` | `/api/v1/orchestration/tasks/{task_id}/complete` | Investigator+ | Convenience endpoint to complete task |
| `GET` | `/api/v1/orchestration/cases/{case_id}/checklist` | Analyst+ | Get case checklist items |
| `POST` | `/api/v1/orchestration/cases/{case_id}/checklist` | Investigator+ | Add item to case checklist |
| `PUT` | `/api/v1/orchestration/cases/{case_id}/checklist/{item_id}`| Investigator+ | Check/uncheck case checklist item |
| `GET` | `/api/v1/orchestration/timeline/{case_or_entity_id}` | Analyst+ | Get unified forensic intelligence timeline |
| `GET` | `/api/v1/orchestration/related-cases/{case_id}` | Analyst+ | Discover linked investigation cases |
| `GET` | `/api/v1/orchestration/recommendations/{case_id}` | Analyst+ | Get advisory next-step recommendations |
| `GET` | `/api/v1/orchestration/search` | Analyst+ | Bounded search across entities, alerts, cases |

---

## 6. Performance Benchmarks

100-run empirical benchmarks verified on Windows / Python 3.14.7:

* **Alert Correlation Latency**: P95 = **0.006 ms** (Target <20ms)
* **Priority Score Calculation**: P95 = **0.019 ms** (Target <15ms)
* **Evidence Tier Ranking**: P95 = **0.023 ms** (Target <25ms)
* **Investigation Brief Synthesis**: P95 = **0.094 ms** (Target <30ms)
* **Forensic Timeline Assembly**: P95 = **0.026 ms** (Target <25ms)
* **End-to-End Orchestration Execution**: P95 = **0.188 ms** (Target <50ms)
* **Jitter / Stability**: Maximum standard deviation across all operations = **0.019 ms**

Full benchmark details in `docs/performance/phase-19.md`.
