# FinGraph Architecture — Phase 17: Autonomous Fraud Intelligence, Adaptive Detection & Threat Propagation

## 1. Architectural Overview

Phase 17 elevates the FinGraph platform from enterprise fraud investigation into a continuously self-improving, explainable **Autonomous Fraud Intelligence Platform**. The platform autonomously scans for uncovered structural motifs, synthesizes adaptive detector proposals, validates candidate detectors in a non-destructive shadow sandbox, calibrates risk scoring thresholds against empirical investigation outcomes, and models multi-hop threat propagation contagion.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               GRAPH & TRANSACTION TELEMETRY            │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                    [Detection Gap Finder]
                                                │
                                                ▼
                        ┌────────────────────────────────────────────────┐
                        │             DISCOVERED DETECTION GAPS          │
                        │  - Structural Cycles     - Centrality Spikes   │
                        │  - Proxy Hopping         - Dense Communities   │
                        └───────────────────────┬────────────────────────┘
                                                │
                                  [Adaptive Recommendation Engine]
                                                │
                                                ▼
                        ┌────────────────────────────────────────────────┐
                        │         ADAPTIVE DETECTOR PROPOSALS            │
                        │  Status: PROPOSED -> UNDER_REVIEW              │
                        └───────┬───────────────────────────────┬────────┘
                                │                               │
                   [Shadow Detector Sandbox]          [Risk Calibration Engine]
                                │                               │
                                ▼                               ▼
                        ┌────────────────┐             ┌────────────────┐
                        │ SHADOW RESULTS │             │ 5-BUCKET MATRIX│
                        │ (Non-Prod Eval)│             │ & DRIFT GAUGES │
                        └───────┬────────┘             └────────┬───────┘
                                │                               │
                                └───────────────┬───────────────┘
                                                │
                                    [Human Approval Gate]
                                      (Admin Authority)
                                                │
                                                ▼
                        ┌────────────────────────────────────────────────┐
                        │            DEPLOYED DETECTOR VERSION           │
                        │        Immutable Detector Registry (v2.x)      │
                        └───────────────────────┬────────────────────────┘
                                                │
                                    [Threat Propagation Engine]
                                                │
                                                ▼
                        ┌────────────────────────────────────────────────┐
                        │         MULTI-HOP CONTAGION MODELING           │
                        │  6-Factor Contagion Index (0-100) & Topology   │
                        └────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Autonomous Intelligence & Gap Discovery
* **`DetectionGapFinder`**: Scans transaction graphs, structural motifs, and unflagged anomalies to identify blindspots where suspicious activity falls just below existing rule cutoffs.
* **`AdaptiveRecommendationEngine`**: Synthesizes deterministic tuning suggestions, rule additions, and parameter adjustments.
* **Human Approval Gate**: Strict RBAC enforcement. Proposed changes start in `PROPOSED` and transition to `UNDER_REVIEW` (Investigator), requiring `ADMIN` authority to reach `APPROVED` and `DEPLOYED`.
* **Immutable Detector Versioning**: Every deployed recommendation archives an immutable `DetectorVersion` record with full rationale and configuration history.

### 2.2 Shadow Detector Simulation Sandbox
* **`ShadowDetectorSimulator`**: Safely evaluates proposed rule parameters over historical transactions and alerts without modifying production data or triggering alerts.
* **Ground Truth Flagging**: Flags runs as `INSUFFICIENT_GROUND_TRUTH` when verified labels are absent, preventing fabricated precision/recall metrics.

### 2.3 Empirical Risk Calibration
* **`RiskCalibrator`**: Partitions risk scores into 5 monotonic buckets (`0-20`, `21-40`, `41-60`, `61-80`, `81-100`) and maps them against investigator verdicts to measure empirical confirmation rates and false positive rates.
* **Threshold Suggestions**: Computes optimal cutoffs to reduce investigator alert fatigue while retaining high-risk fraud cases.

### 2.4 Multi-Hop Threat Propagation
* **`ThreatPropagationEngine`**: Simulates contagion progression from an origin entity across $k$ hops (up to 5), generating step-by-step timelines ($T_0 	o T_3$), exposure deltas, and D3-compatible node/edge topologies.
* **6-Factor Propagation Score**:
  $$\text{PropagationScore} = 0.25 \cdot \text{SpeedVelocity} + 0.20 \cdot \text{AffectedCount} + 0.20 \cdot \text{Centrality} + 0.15 \cdot \text{Exposure} + 0.10 \cdot \text{RiskEscalation} + 0.10 \cdot \text{TemporalDensity}$$
