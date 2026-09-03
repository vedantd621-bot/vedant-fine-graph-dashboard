# FinGraph Architecture: Phase 8 — Investigation API & React Dashboard

Phase 8 bridges the analytical graph engine with human fraud analysts and compliance teams through a high-performance REST API and an analyst-centric React workstation.

---

## 1. End-to-End System Flow

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Python          │       │ Apache Kafka    │       │ Apache Flink    │
│ Simulator       │ ────► │ Topic:          │ ────► │ Stateful Stream │
│ 5 Topologies    │       │ 'transactions'  │       │ Micro-batching  │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │ Neo4j 5.18 GDS  │
                                                    │ Graph Store     │
                                                    └────────┬────────┘
                                                             │
                                        ┌────────────────────┴────────────────────┐
                                        ▼                                         ▼
                             ┌─────────────────────┐                   ┌─────────────────────┐
                             │ Cypher Detection    │                   │ Neo4j GDS Analytics │
                             │ Engine (7 Patterns) │                   │ PageRank / WCC / LV │
                             └──────────┬──────────┘                   └──────────┬──────────┘
                                        │                                         │
                                        └────────────────────┬────────────────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │ Explainable     │
                                                    │ Risk Engine     │
                                                    │ (rule-gds-v1)   │
                                                    └────────┬────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │ FastAPI Backend │
                                                    │ REST Services   │
                                                    └────────┬────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │ React 18 + D3   │
                                                    │ Investigation   │
                                                    │ Dashboard       │
                                                    └─────────────────┘
```

---

## 2. Key System Guarantees

1. **Strict No-Fake-Data Enforcement**:
   - The React frontend consumes exclusively backend REST endpoints powered by Neo4j data and real-time risk engine calculations.
2. **Deterministic Bounded Traversals**:
   - Subgraph queries parameterize traversal depth ($1..3$) and limit nodes/edges to prevent database resource exhaustion.
3. **Traceability & Explainability**:
   - Every risk score includes an audit trail of underlying rule flags, PageRank centrality values, and human-readable natural language reasons.
4. **Interactive Graph Forensics**:
   - Graph visualization accurately reflects directional transfers with amounts, accounts, bank hosting, and person ownership.
