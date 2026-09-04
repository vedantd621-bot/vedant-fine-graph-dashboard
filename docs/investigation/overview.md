# FinGraph Advanced Fraud Intelligence & Investigation Overview

## Introduction

FinGraph Phase 11 expands the platform into an enterprise-grade **Fraud Intelligence & Decision-Support Workspace**. It bridges streaming graph detection, graph data science (GDS), explainable risk analytics, and compliance workflows into a unified, evidence-grounded investigation ecosystem.

```text
┌─────────────────────────────── FinGraph Phase 11 Intelligence Architecture ───────────────────────────────┐
│                                                                                                          │
│   Kafka Streams ──► Apache Flink (Stateful Sink) ──► Neo4j Labeled Property Graph                        │
│                                                              │                                            │
│                                                              ▼                                            │
│                                                   Cypher Pattern Detectors                                │
│                                                   & Neo4j GDS Engine                                      │
│                                                              │                                            │
│                                                              ▼                                            │
│   ┌──────────────────────────────────────── Intelligence Core ────────────────────────────────────────┐  │
│   │                                                                                                   │  │
│   │   • Entity Risk Profiling (Ranked factors, PageRank centrality, connectivity)                     │  │
│   │   • Evidence-Grounded Explainability (Deterministic weights & raw entity refs)                    │  │
│   │   • Unified Forensic Timelines (Merged transactions, detections, alerts, cases, audit logs)       │  │
│   │   • Syndicate Alert Correlation (Shared counterparties, Louvain clusters, detector hits)          │  │
│   │   • Actionable Recommendations (INSPECT_TRAIL, FREEZE_ACCOUNT, REVIEW_COUNTERPARTIES)             │  │
│   │   • Bounded Graph Neighborhoods (Filtered k-hop subgraphs, shared counterparties)                 │  │
│   │                                                                                                   │  │
│   └──────────────────────────────────────────────────┬────────────────────────────────────────────────┘  │
│                                                      │                                                    │
│                                                      ▼                                                    │
│   ┌──────────────────────────────────────── Workflow & Audit ─────────────────────────────────────────┐  │
│   │                                                                                                   │  │
│   │   • Case Management Lifecycle (OPEN ➔ IN_PROGRESS ➔ ESCALATED ➔ RESOLVED ➔ CLOSED)                 │  │
│   │   • Cryptographic Evidence Vault (SHA-256 integrity digests, immutable provenance)                │  │
│   │   • Investigator Assignment & Chronological Note Threads                                          │  │
│   │   • Strict RBAC Enforcement (ADMIN, INVESTIGATOR, ANALYST) & Tamper-Evident Audit Trail           │  │
│   │                                                                                                   │  │
│   └──────────────────────────────────────────────────┬────────────────────────────────────────────────┘  │
│                                                      │                                                    │
│                                                      ▼                                                    │
│   ┌────────────────────────────────────── Interfaces & Streams ───────────────────────────────────────┐  │
│   │                                                                                                   │  │
│   │   • FastAPI REST v1 Endpoints (Cases, Intelligence, Graphs, Accounts, Alerts)                     │  │
│   │   • Real-Time EventBus & WebSocket Broadcasts (Live case status, freeze containment)              │  │
│   │   • Investigation React UI (Interactive drawer, timeline visualization, graph exploration)       │  │
│   │                                                                                                   │  │
│   └───────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Capabilities

1. **Entity Risk Profiling & Explainability**:
   - Computes deterministic dossiers combining GDS PageRank centrality, Louvain community clustering, degree topology, Cypher detector hits, and linked cases.
   - Provides clear, human-readable explanations with mathematical weights and raw evidence keys.

2. **Unified Forensic Timelines**:
   - Synthesizes transactions, detector triggers, alert lifecycle events, administrative freeze containment actions, and case notes into a single chronological feed.

3. **Syndicate Correlation & Next-Best-Action Recommendations**:
   - Evaluates multi-alert graph overlap to uncover distributed fraud syndicates and mule clusters.
   - Prescribes concrete operational actions based on confidence and severity thresholds.

4. **Cryptographic Case Management**:
   - Manages case progression with state-machine validations.
   - Seals forensic evidence items with SHA-256 digests to guarantee chain-of-custody integrity.
