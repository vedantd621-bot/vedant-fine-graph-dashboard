# FinGraph Cypher Fraud Detection Engine

## 1. Overview
The FinGraph Cypher Fraud Detection Engine is a rule-based, topology-aware detection layer operating directly on top of the Neo4j financial property graph. It identifies complex multi-entity money laundering topologies with sub-second execution speeds.

```
       +-------------------------------------------------------------+
       |                  DetectionEngine.run_all()                  |
       +-------------------------------------------------------------+
          │               │               │               │
          ▼               ▼               ▼               ▼
    +-----------+   +-----------+   +-----------+   +-----------+
    |  Funnel   |   |One-to-Many|   |   Chain   |   | Circular  |
    | Detector  |   | Detector  |   | Detector  |   | Detector  |
    +-----------+   +-----------+   +-----------+   +-----------+
          │               │               │               │
          └───────────────┴───────┬───────┴───────────────┘
                                  │
                                  ▼
                    +---------------------------+
                    |  DetectionResult Models   |
                    | (Explainable Evidence)    |
                    +---------------------------+
                                  │
                                  ▼
                    +---------------------------+
                    |   Deduplicated Alerts     |
                    |  (SHA256 Fingerprints)    |
                    +---------------------------+
```

---

## 2. Detectors & Graph Topologies

### 1. Funnel / Smurfing (`FUNNEL`)
- **Topological Pattern**: Multiple source accounts transfer structured sub-$10,000 amounts to an intermediary mule, which subsequently sweeps out the aggregated total to an exit account ($A_1, A_2, A_3 \to I \to D$).
- **Parameters**: `min_sources` (default 3), `min_total_amount`, `start_time`, `end_time`.
- **Severity**: `HIGH` / `CRITICAL` ($> \$30,000$ or $\ge 5$ sources).

### 2. One-to-Many Distribution (`ONE_TO_MANY`)
- **Topological Pattern**: Single high-value source account rapidly disburses funds to multiple recipient accounts ($S \to B_1, B_2, B_3, B_4$).
- **Parameters**: `min_destinations` (default 4), `min_total_amount`, `start_time`, `end_time`.
- **Severity**: `MEDIUM` / `HIGH`.

### 3. Intermediary Chain Layering (`CHAIN`)
- **Topological Pattern**: Linear pass-through sequences ($A \to B \to C \to D \to E$) designed to break audit trails across financial institutions.
- **Parameters**: `min_depth` (default 3), `max_depth` (default 6).
- **Severity**: `MEDIUM` (3 hops), `HIGH` ($\ge 4$ hops).

### 4. Circular Flow Wash Trading (`CIRCULAR_FLOW`)
- **Topological Pattern**: Closed-loop transaction paths where funds return to origin accounts ($A \to B \to C \to A$).
- **Rotational Deduplication**: Canonicalizes cyclic rotations (`[B, C, A, B]` $\to$ `[A, B, C, A]`) to ensure one unique alert per cycle.
- **Severity**: `CRITICAL`.

### 5. Layered Multi-Tier Network (`LAYERED_NETWORK`)
- **Topological Pattern**: 4-tier syndicate: Sources $\to$ Intermediaries $\to$ Central Aggregator $\to$ Exit Destinations.
- **Severity**: `CRITICAL`.

### 6. High-Degree Hub (`HIGH_DEGREE`)
- **Topological Pattern**: Accounts with disproportionately high total network degree ($\text{in-degree} + \text{out-degree} \ge \text{min\_degree}$).
- **Severity**: `MEDIUM` / `HIGH`.

### 7. Forensic Money Trail (`MONEY_TRAIL`)
- **Purpose**: Targeted multi-hop path discovery between two accounts ($A \to B$) or exploratory path walks outwards from an account.
