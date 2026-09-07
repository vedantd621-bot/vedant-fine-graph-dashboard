# FinGraph Master Enterprise Architecture & System Topology

---

## 1. Architectural Overview

The **FinGraph Master Enterprise Fraud Intelligence Platform** unifies streaming ingestion, graph topological pattern detection, explainable risk scoring, cryptographic case management, intelligence orchestration, autonomous detection governance, multi-tenant control planes, and executive intelligence into a single production system.

```text
                               +---------------------------------------+
                               |     Client / Investigation UI         |
                               | (React 18 + TypeScript + D3.js)       |
                               +---------------------------------------+
                                                   |
                                                   v [JWT Bearer + X-Tenant-ID]
+===================================================================================================+
|                                  FINGRAPH ENTERPRISE CONTROL PLANE                                 |
+===================================================================================================+
|                                                                                                   |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|   |  Tenant Context Injector | -> |  Extended RBAC (9 Roles) | -> |  Deterministic Policy     |   |
|   |  (Fast Header/Token Res) |    |  (31 Granular Perms)     |    |  Engine (Default Deny)    |   |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|                 |                                                               |                 |
|                 v                                                               v                 |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|   | Tenancy Service          |    | Decisioning & Sandbox    |    | Multi-Tenant Routing      |   |
|   | - 5-Level Hierarchy      |    | - Deterministic Verdicts |    | - Cross-Tenant Blocker    |   |
|   | - Quotas & Telemetry     |    | - Immutable Overrides    |    | - Scoped Storage & WS     |   |
|   | - Config Versioning      |    | - What-If Sandbox        |    | - Scoped Audit Ledger     |   |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|                                                                                                   |
+===================================================================================================+
                                                   |
                                                   v
+===================================================================================================+
|                                    CORE PLATFORM INTELLIGENCE                                     |
+===================================================================================================+
|                                                                                                   |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|   | Ingestion & Streaming    | -> | Cypher & GDS Analytics   | -> | Risk & Behavioral Engine  |   |
|   | - Kafka (KRaft Mode)     |    | - 7 Graph Detectors      |    | - Explainable 0-100 Score |   |
|   | - Apache Flink (CEP/DLQ) |    | - Louvain / PageRank/WCC |    | - 5m to 30d Baselines     |   |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|                 |                                                               |                 |
|                 v                                                               v                 |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|   | Intelligence Orchestr    |    | Case Intelligence        |    | Autonomous Governance     |   |
|   | - Cross-Alert Correlator |    | - Cryptographic Vault    |    | - Adaptive Detector Gap   |   |
|   | - 6-Factor Priority Sc   |    | - 7-State Lifecycle      |    | - Shadow Testing Sandbox  |   |
|   | - Automated Dossier Brief|    | - Multi-Investigator RBAC|    | - Human-in-Loop Approval  |   |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|                                                                                                   |
+===================================================================================================+
                                                   |
                                                   v
+===================================================================================================+
|                                 ENTERPRISE ANALYTICS & REPORTING                                  |
+===================================================================================================+
|                                                                                                   |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|   | Enterprise Analytics     |    | Reporting Center         |    | Executive Posture Center  |   |
|   | - Multi-Tenant KPI Sets  |    | - 8 Report Types         |    | - 0-100 Threat Index      |   |
|   | - Time-Series Trends     |    | - SHA-256 Snapshots      |    | - Driver Attribution      |   |
|   | - KPI Anomaly Detection  |    | - CSV Formula Neutralize |    | - Evidence-Backed Insights|   |
|   +--------------------------+    +--------------------------+    +---------------------------+   |
|                                                                                                   |
+===================================================================================================+
```

---

## 2. Multi-Tenant Domain Boundary

The platform enforces isolation across a strict 5-level organizational hierarchy:
1. **Platform**: Global operational layer managed by `PLATFORM_ADMIN`.
2. **Tenant**: Root isolation customer boundary (e.g. Acme Financial Group).
3. **Organization**: Regional or subsidiary entity (e.g. Acme EMEA).
4. **Business Unit**: Functional division (e.g. Retail AML Division).
5. **Investigation Team**: Operational squad (e.g. High-Risk ATO Team).
6. **User**: Authenticated subject assigned team roles (`LEAD`, `SENIOR`, `ANALYST`, `TRAINEE`).
