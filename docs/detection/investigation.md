# FinGraph Fraud Investigation Workflow

This document outlines the standard operating procedure (SOP) for compliance officers and fraud analysts using FinGraph.

```
       +---------------------------------------------+
       |   1. Alert Triggered by Detection Engine    |
       +---------------------------------------------+
                              │
                              ▼
       +---------------------------------------------+
       |     2. Analyst Triage & Evidence Review     |
       |  - Pattern type (Funnel, Cycle, Chain, etc.)|
       |  - Severity & Confidence Score              |
       |  - Source & Destination accounts            |
       +---------------------------------------------+
                              │
                              ▼
       +---------------------------------------------+
       |        3. Forensic Money Trail Tracing      |
       |  - MoneyTrailInvestigator (max_hops 1..4)   |
       |  - Timestamp temporal sequence inspection   |
       +---------------------------------------------+
                              │
                              ▼
       +---------------------------------------------+
       |         4. Counterparty & Entity Audit      |
       |  - Person owner identification              |
       |  - Bank institutions & jurisdiction audit   |
       +---------------------------------------------+
                              │
                              ▼
       +---------------------------------------------+
       |          5. Case Action & Status Update     |
       |  - Status: INVESTIGATING / RESOLVED         |
       |  - Simulated Account Freeze (Phase 11)      |
       +---------------------------------------------+
```

---

## Step-by-Step Investigation Walkthrough

### Step 1: Alert Trigger & Ingestion
When a transaction stream creates or completes a suspicious topology in Neo4j, `DetectionEngine.run_all()` detects the graph pattern and generates a deduplicated `Alert` (status: `OPEN`).

### Step 2: Evidence Inspection
The analyst examines the `evidence` payload:
- `metric_name`: e.g. `source_count`, `hop_count`, `cycle_length`
- `metric_value` vs `threshold_value`
- `inflow_amount` and `outflow_amount`
- `reason_summary`

### Step 3: Multi-Hop Trail Tracing
The analyst runs the Money Trail investigator:
```bash
python -m detection.src.cli --money-trail --from-account A001 --to-account A006
```

### Step 4: Decision & Simulated Freeze
If confirmed as an active syndicate operation, the analyst marks the alert status as `INVESTIGATING` and initiates a simulated account freeze via the investigation dashboard.
