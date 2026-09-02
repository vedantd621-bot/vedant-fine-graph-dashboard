# FinGraph System Architecture

## 1. Executive Summary
FinGraph is an enterprise-grade real-time Anti-Money Laundering (AML) and fraud detection platform. It couples distributed streaming technologies with graph database analytics to uncover complex fraud topologies that bypass conventional relational SQL monitoring.

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                            DATA GENERATION & INGESTION                            |
|                                                                                   |
|  +-------------------------------------+        +------------------------------+  |
|  | Python Synthetic Generator          |        | Apache Kafka Cluster         |  |
|  | - Retail Normal Traffic             |------->| - Topic: 'transactions'      |  |
|  | - Smurfing, Cycles, Layering, Fans  |        | - Partitioned by account_id  |  |
|  +-------------------------------------+        +------------------------------+  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                            STREAM PROCESSING & ENRICHMENT                         |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Apache Flink Streaming Engine                                               |  |
|  | - JSON Deserialization & Strict Schema Validation                           |  |
|  | - Malformed Record Filtering / Dead-letter logging                          |  |
|  | - Timestamp Normalization & ISO-8601 parsing                                |  |
|  | - Micro-batching & Graph Upsert Operations                                  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                            GRAPH STORAGE & GRAPH ANALYTICS                        |
|                                                                                   |
|  +------------------------------------+    +-----------------------------------+  |
|  | Neo4j 5.x Graph Database           |    | Neo4j Graph Data Science (GDS)    |  |
|  | - Nodes: Person, Account, Bank     |<-->| - PageRank Centrality             |  |
|  | - Edges: OWNS, HOSTED_BY,          |    | - Louvain Community Detection     |  |
|  |          TRANSFERRED_TO            |    | - Weakly Connected Components     |  |
|  | - Sub-100ms Cypher Query Library   |    | - Memory Graph Projections        |  |
|  +------------------------------------+    +-----------------------------------+  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                            RISK ENGINE & API SERVICES                             |
|                                                                                   |
|  +-------------------------------------+        +------------------------------+  |
|  | Explainable Risk Scoring Service    |        | FastAPI Backend Server       |  |
|  | - 0-100 Multi-Signal Formula        |------->| - Graph Subgraph API         |  |
|  | - Low / Medium / High / Critical    |        | - Investigation Records      |  |
|  +-------------------------------------+        | - Audit Log Store            |  |
|                                                 +------------------------------+  |
+-----------------------------------------------------------------------------------+
                         │                                       │
                         ▼                                       ▼
+------------------------------------+      +---------------------------------------+
| ALERT ENGINE                       |      | ANALYST INVESTIGATION DASHBOARD       |
| - Severity Thresholds (60/80)      |      | - Force-directed D3 Graph             |
| - Cooldown & Deduplication         |      | - Money Trail Tracer                  |
| - Mock / Slack / Email Webhooks    |      | - Community Syndicate Explorer        |
+------------------------------------+      | - Simulated Freeze Syndicate Action   |
                                            +---------------------------------------+
```

## 3. Subsystem Breakdown

### 3.1. Synthetic Transaction Generator
Emits high-fidelity JSON events containing `transaction_id`, `timestamp`, `from_account`, `to_account`, `amount`, `currency`, `from_person`, `to_person`, `bank`, and `scenario_id`.

### 3.2. Apache Kafka
Serves as the high-throughput, low-latency buffer decoupling data producers from downstream consumers. Configured with KRaft consensus.

### 3.3. Apache Flink
Applies stateful stream processing, validates payloads against strict typing, rejects corrupt data, and streams upserts into Neo4j.

### 3.4. Neo4j & Graph Data Science (GDS)
Maintains the canonical graph model. Cypher indexes and constraints guarantee high query velocity ($<100\text{ ms}$). GDS detects community clusters (Louvain) and structural importance (PageRank).

### 3.5. Risk Scoring Engine
Transparently computes risk scores from 0 to 100 without opaque "black box" claims. Factors include degree centrality, cycle detection, community size, and transactional velocity.

### 3.6. FastAPI Backend
Exposes performant REST endpoints supplying graph nodes, edges, alerts, and audit trails.

### 3.7. React / D3 Dashboard
Interactive interface tailored for compliance officers to visually dissect syndicates, highlight money trails, and trigger simulated freeze actions.
