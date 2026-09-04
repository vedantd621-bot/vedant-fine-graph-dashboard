# FinGraph v1.0 Complete Platform Architecture

## 1. Architectural Blueprint

FinGraph is an enterprise-grade, real-time graph intelligence, fraud detection, and autonomous investigation operations platform.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 INGESTION & STREAMING                                  │
│  [Simulated / Live Transactions] ──► [Kafka Topic: transactions] ──► [Flink Window]   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              GRAPH PERSISTENCE & STORAGE                               │
│  [Neo4j 5.x Graph Database] ◄── Cypher Engine ── (Accounts, Transactions, Devices)     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                FRAUD INTELLIGENCE CORE                                 │
│  [Cypher Detectors] ─► [GDS Graph Analytics] ─► [Explainable Risk Engine (0-100)]      │
│  - Circular Flow       - Louvain Communities    - Multi-Factor Hazard Scoring          │
│  - Smurfing Fanout     - PageRank Centrality    - Monotonic Calibration Matrix         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           OPERATIONS & TRIAGE MANAGEMENT                               │
│  [Alert Prioritization Engine] ─► [Investigator Queue & SLA] ─► [Case Intelligence]    │
│  - Dynamic Hazard Ranking         - Breach Warnings             - Evidence Graphs      │
│  - Auto-Deduplication             - Workload Allocation         - Multi-Case Campaigns │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     AUTONOMOUS INTELLIGENCE & THREAT PROPAGATION                       │
│  [Gap Discovery Engine] ──► [Adaptive Recs] ──► [Shadow Sandbox] ──► [Admin Gate]      │
│  - Micro-Cycle Motifs        - Parameter Tune    - Non-Destructive    - Version v2.x   │
│  - Proxy Hopping             - Rule Drafts       - Ground Truth Gate  - Deployment     │
│                              └──────────────────► [Multi-Hop Contagion Explorer]       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                PRESENTATION & WEBSOCKET                                │
│  [FastAPI REST API (24 Routers)] ◄──► [Real-Time WebSocket Bus] ◄──► [React Workstation│
└────────────────────────────────────────────────────────────────────────────────────────┘
```
