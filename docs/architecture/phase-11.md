# FinGraph Phase 11 System Architecture

## Architectural Evolution

Phase 11 integrates deep graph intelligence with full-lifecycle case management and compliance tooling:

```text
                               ┌────────────────────────┐
                               │   Streaming Pipeline   │
                               │ (Kafka ➔ Flink ➔ Neo4j)│
                               └───────────┬────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │            Graph Analytics Layer        │
                      │  • 7 Cypher Pattern Detectors           │
                      │  • Neo4j GDS (PageRank, Louvain, WCC)   │
                      │  • Explainable Risk Engine              │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │      Phase 11 Intelligence Core         │
                      │  • IntelligenceService                  │
                      │  • CaseService (State Machine & Vault)  │
                      │  • GraphService (Filtered Neighborhoods)│
                      │  • AuditService (Tamper-evident logs)   │
                      │  • EventBus (Realtime Pub/Sub)          │
                      └────────────────────┬────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
             ┌─────────────────────┐               ┌─────────────────────┐
             │ FastAPI REST API    │               │ WebSocket Server    │
             │ (/api/v1/cases)     │               │ (/api/v1/ws)        │
             │ (/api/v1/entities)  │               │ Live Updates        │
             │ (/api/v1/graph)     │               │ Live Alerts         │
             └──────────┬──────────┘               └──────────┬──────────┘
                        │                                     │
                        └──────────────────┬──────────────────┘
                                           ▼
                               ┌───────────────────────┐
                               │  React Investigation  │
                               │       Dashboard       │
                               │  • Cases Workspace    │
                               │  • Forensic Timeline  │
                               │  • Evidence Registry  │
                               │  • D3 Graph Explorer  │
                               └───────────────────────┘
```

---

## API Endpoints Added in Phase 11

### Case Management (`/api/v1/cases`)
- `POST /api/v1/cases`: Create case with initial metadata.
- `GET /api/v1/cases`: List & filter cases by status, priority, investigator, or entity.
- `GET /api/v1/cases/{case_id}`: Retrieve comprehensive case dossier with notes and evidence.
- `PATCH /api/v1/cases/{case_id}`: Mutate case status or priority (RBAC gated).
- `POST /api/v1/cases/{case_id}/assign`: Assign case to an investigator.
- `POST /api/v1/cases/{case_id}/notes`: Append investigator note to chronological thread.
- `POST /api/v1/cases/{case_id}/evidence`: Attach cryptographically hashed evidence item.
- `POST /api/v1/cases/{case_id}/alerts`: Link alert to case.
- `DELETE /api/v1/cases/{case_id}/alerts/{alert_id}`: Unlink alert.
- `POST /api/v1/cases/{case_id}/accounts`: Link account entity to case.
- `DELETE /api/v1/cases/{case_id}/accounts/{account_id}`: Unlink account.
- `GET /api/v1/cases/{case_id}/timeline`: Retrieve unified forensic timeline for case.

### Fraud Intelligence (`/api/v1/entities`, `/api/v1/alerts`, `/api/v1/investigation`)
- `GET /api/v1/entities/{id}/risk-profile`: Multi-dimensional risk dossier.
- `GET /api/v1/entities/{id}/risk-explanation`: Ranked explainable risk factors.
- `GET /api/v1/entities/{id}/timeline`: Unified chronological forensic stream.
- `GET /api/v1/alerts/{id}/correlated`: Syndicate correlation across related alerts.
- `GET /api/v1/alerts/{id}/recommendations`: Prescriptive investigation next steps.
- `GET /api/v1/investigation/analytics`: Platform-wide case, alert, and syndicate metrics.

### Graph Investigation (`/api/v1/graph`)
- `GET /api/v1/graph/neighborhood/{account_id}`: Bounded k-hop neighborhood graph.
- `GET /api/v1/graph/suspicious-neighborhood/{account_id}`: Filtered subgraph with risk $\ge 60.0$.
- `GET /api/v1/graph/common-counterparties`: Shared transaction counterparties between two accounts.
