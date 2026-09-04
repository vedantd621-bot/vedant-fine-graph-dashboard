# FinGraph v1.0 End-to-End Demo Walkthrough Script

A 15-minute forensic investigation and autonomous intelligence demonstration.

---

### Step 1: Authentication & Executive Command Center (2 min)
1. Navigate to `/login`. Sign in as `admin` / `Admin@123` or `investigator` / `Investigator@123`.
2. Inspect the **Enterprise Command Center V2** dashboard:
   - Enterprise Threat Index gauge ($0-100$).
   - Active campaigns, unflagged early warnings, and SLA triage metrics.

### Step 2: Proactive Early Warning Triage (2 min)
1. Open the **Early Warning Center** (`/early-warnings`).
2. Review proactive warnings generated before alert firing (e.g. `WARN-VEL-001` velocity hazard).
3. Acknowledge warning with forensic notes or escalate directly into an Investigation Case.

### Step 3: Alert Queue & SLA Prioritization (3 min)
1. Navigate to **Alert Queue & Triage** (`/queue`).
2. Review prioritized P1 Critical alerts (e.g. `ALT-CIRC-01` circular wash flow).
3. Inspect the automated risk factors ($88.5/100$), evidence reference, and SLA deadline counter.
4. Execute triage decision: Assign to investigator, adjust priority, or escalate.

### Step 4: Multi-Case Intelligence & Evidence Graph (3 min)
1. Open **Case Intelligence** (`/case-intelligence`).
2. Select campaign `CMP-2026-001` to view cross-case shared infrastructure.
3. Review interactive Subgraph Evidence graph, device fingerprint matches, and IP overlaps.
4. Add collaborative investigator notes in the forensic comment thread.

### Step 5: Autonomous Intelligence & Shadow Simulation (3 min)
1. Open **Adaptive Intelligence** (`/adaptive-intelligence`).
2. Trigger **Scan Detection Gaps** to uncover sub-threshold structural cycles and proxy hops.
3. Click **Run Shadow Simulation** on proposed detector rule `rec_tune_cycle_...`.
4. Inspect sandbox findings (evaluating 10,800 historical transactions with 0 false positive alerts in prod).
5. As Admin, approve and deploy the recommendation to create a registered `DetectorVersion`.

### Step 6: Multi-Hop Threat Propagation (2 min)
1. Open **Threat Propagation** (`/threat-propagation`).
2. Input origin entity `acc_881` and execute 3-hop contagion simulation.
3. Inspect 6-factor propagation index ($84.2/100$), timeline steps ($T_0 	o T_3$), and D3 topology graph.
4. Review automated containment recommendations (immediate administrative hold, node quarantine).
