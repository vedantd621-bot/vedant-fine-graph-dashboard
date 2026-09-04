# FinGraph Phase 12 Architecture — Fraud Network Intelligence, Behavioral Anomaly & ML-Ready Analytics

## Architecture Overview

```text
               ┌───────────────────────────────┐
               │    Transaction Simulator      │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │         Kafka Stream          │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │         Apache Flink          │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │          Neo4j Graph          │
               └───────────────┬───────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ Cypher Rules   │     │ GDS Algorithms │     │ Risk Engine    │
│ (Flow Rings,   │     │ (PageRank,     │     │ (Explainable   │
│  Funnels,      │     │  Louvain,      │     │  Factor        │
│  Chains)       │     │  WCC)          │     │  Scoring)      │
└───────┬────────┘     └───────┬────────┘     └───────┬────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
       ┌───────────────────────────────────────────────┐
       │             Phase 12 Services                 │
       │  ┌─────────────────────────────────────────┐  │
       │  │ Network Intelligence Service            │  │
       │  │ (Syndicate Discovery, 5-Factor Risk,    │  │
       │  │  Role Inference, Case Promotion)        │  │
       │  ├─────────────────────────────────────────┤  │
       │  │ Behavioral Anomaly Service              │  │
       │  │ (30d Baselines, 5 Window Deviations,   │  │
       │  │  Explainable Peer Similarity)           │  │
       │  ├─────────────────────────────────────────┤  │
       │  │ ML Feature Generation Service           │  │
       │  │ (18 Normalized Signals, CSV/JSON Export)│  │
       │  └─────────────────────────────────────────┘  │
       └───────────────────────┬───────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ REST Endpoints │     │ Realtime Bus   │     │ React UI       │
│ /networks      │     │ (network.*,    │     │ Fraud Networks │
│ /behavior      │     │  anomaly.*)    │     │ Detail Views   │
│ /features      │     │ WebSockets     │     │ Behavioral Tab │
└────────────────┘     └────────────────┘     └────────────────┘
```

---

## REST Endpoints Summary

### Fraud Networks (`/api/v1/networks`)
- `GET /api/v1/networks`: Filtered, paginated list of discovered fraud syndicates.
- `POST /api/v1/networks/discover`: Triggers network discovery scan.
- `GET /api/v1/networks/{id}`: Detailed network dossier with metrics and member accounts.
- `GET /api/v1/networks/{id}/members`: Constituent members with inferred roles and centrality metrics.
- `GET /api/v1/networks/{id}/subgraph`: Interactive D3 graph payload.
- `GET /api/v1/networks/{id}/risk-explanation`: Deterministic 5-factor mathematical score breakdown.
- `GET /api/v1/networks/{id}/evidence`: Forensic timeline and detection items.
- `POST /api/v1/networks/{id}/create-case`: Promotes network to case (RBAC: `INVESTIGATOR` or `ADMIN`).

### Behavioral Anomalies (`/api/v1/entities`)
- `GET /api/v1/entities/{id}/behavior`: Windowed anomaly deviations (`5m`, `1h`, `24h`, `7d`, `30d`).
- `GET /api/v1/entities/{id}/baseline`: 30-day statistical baseline metrics.
- `GET /api/v1/entities/{id}/similar`: Explainable top-k similar suspect entities.

### ML Feature Store (`/api/v1/features`)
- `GET /api/v1/features/catalog`: Catalog of 18 feature definitions.
- `GET /api/v1/features/entity/{id}`: Normalized feature vector for a specific account.
- `POST /api/v1/features/export`: Batch CSV / JSON tabular export.
