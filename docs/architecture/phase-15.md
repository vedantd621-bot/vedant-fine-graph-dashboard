# Architecture — Phase 15: Enterprise Fraud Command Center, Case Intelligence & Investigation Collaboration

## 1. Overview & Vision

FinGraph Phase 15 elevates the platform from transactional and alert triage into a complete **Enterprise Fraud Command Center**. It coordinates multi-case intelligence, bounded forensic relationship graph synthesis, deterministic fraud campaign clustering with 6-factor risk scoring, multi-investigator collaborative permissions, auditable case commenting with soft-delete semantics, immutable chronological activity audit feeds, and an executive 0–100 Enterprise Fraud Posture evaluation.

```
+----------------------------------------------------------------------------------------------------+
|                                    FinGraph Phase 15 Architecture                                   |
+----------------------------------------------------------------------------------------------------+
                                      |
                     Cases + Alerts + Fraud Networks + Behavioral Anomalies
                                      |
                                      v
       +---------------------------------------------------------------+
       |             Cross-Case Intelligence & Correlation             |
       |  - Multi-Signal Case Correlation (Accounts, Counterparties,   |
       |    Networks, Detectors, Behavioral, Temporal, Financial)      |
       |  - Bounded Case Relationship Graph & Subgraphs                |
       |  - Evidence Provenance (SUPPORTS, CONTRADICTS, DERIVED_FROM)  |
       +---------------------------------------------------------------+
                                      |
              +-----------------------+-----------------------+
              |                                               |
              v                                               v
+-----------------------------+               +-------------------------------+
|  Fraud Campaign Discovery   |               |   Investigation Collaboration |
| - Clustering Related Cases  |               | - Multi-Investigator Roles    |
| - 6-Factor Campaign Scoring |               |   (OWNER, COLLABORATOR, WATCH)|
| - Financial Impact Engine   |               | - Auditable Case Comments     |
| - Campaign Lifecycle States |               | - Immutable Activity Timeline |
+-----------------------------+               +-------------------------------+
              |                                               |
              +-----------------------+-----------------------+
                                      |
                                      v
+----------------------------------------------------------------------------------------------------+
|                         Executive Fraud Command Center Engine                                      |
| - Enterprise Fraud Posture Score (0-100) with Positive & Negative Driver Attribution               |
| - Top Active Fraud Campaigns & High-Risk Syndicate Monitoring                                      |
| - Real-Time Collaboration & Campaign WebSocket Event Dispatching                                   |
+----------------------------------------------------------------------------------------------------+
                                      |
                                      v
+----------------------------------------------------------------------------------------------------+
|                   FastAPI Endpoints & React Command Center Workstation                             |
| - REST APIs: /api/v1/case-intelligence/* (Cases, Campaigns, Collaboration, Command Center)        |
| - React UI: FraudCommandCenterPage, CaseIntelligencePage, FraudCampaignDetailPage, Collaboration    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Key Components

### A. Cross-Case Correlation Engine (`backend/app/case_intelligence/correlation.py`)
- Evaluates multi-signal links connecting disparate cases:
  - `SHARED_ACCOUNT`: Direct account overlap across cases.
  - `SHARED_COUNTERPARTY` / `FINANCIAL_FLOW`: Shared directed transaction flow.
  - `SHARED_DETECTOR`: Overlapping topological detector signatures.
  - `TEMPORAL_CLUSTERING`: Cases initiated within tight temporal proximity (<48 hours).

### B. Bounded Case Relationship Graph (`backend/app/case_intelligence/evidence_graph.py`)
- Generates interactive D3 force layouts combining:
  - Cases (`CASE`)
  - Alerts (`ALERT`)
  - Accounts (`ACCOUNT`)
  - Evidence items (`EVIDENCE`)
- Enforces strict bounding limits (`max_nodes=60`, `max_edges=100`) to guarantee sub-millisecond response latencies.

### C. Fraud Campaign Discovery & 6-Factor Risk Scoring (`backend/app/case_intelligence/campaigns.py`)
- Aggregates related cases into syndicate-level campaigns (`CMP-xxxx`).
- Formulates explainable risk score (0–100):
  $$\text{CampaignRisk} = 0.25 \cdot \text{NetworkStrength} + 0.20 \cdot \text{CaseCorrelation} + 0.20 \cdot \text{FinancialExposure} + 0.15 \cdot \text{BehavioralSimilarity} + 0.10 \cdot \text{TemporalConcentration} + 0.10 \cdot \text{EvidenceStrength}$$

### D. Multi-Investigator Collaboration & Audit Trails (`backend/app/case_intelligence/service.py`)
- Role-based permissions on cases: `OWNER`, `COLLABORATOR`, `WATCHER`.
- Case comments with full edit tracking and soft-delete retention.
- Immutable append-only activity feed logging actor, action, timestamp, and request ID.

### E. Executive Fraud Posture Engine (`backend/app/case_intelligence/service.py`)
- Evaluates global enterprise health index (0–100) with explainable positive and negative driver attribution.
