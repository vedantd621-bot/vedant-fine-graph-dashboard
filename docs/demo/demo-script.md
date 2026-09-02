# FinGraph Analyst Demo Script & Walkthrough

This script guides investigators and portfolio reviewers through an interactive fraud syndicate detection demonstration.

## Step 1: System Health Verification
1. Open the FinGraph Dashboard at `http://localhost:3000`.
2. Confirm header status badges:
   - Kafka: Connected (Green)
   - Flink: Running (Green)
   - Neo4j: Connected (Green)
   - Alert Engine: Active (Green)

## Step 2: Live Ingestion & KPI Updates
1. Launch the transaction simulator in a terminal:
   ```bash
   python simulator/src/simulator.py --rate 20 --suspicious-rate 0.25 --duration 30
   ```
2. Observe KPI counters incrementing in real time on the dashboard:
   - Transactions Processed
   - Suspicious Communities Detected
   - Active Critical Alerts

## Step 3: Syndicate Discovery & Force-Graph Inspection
1. Navigate to the **Network View**.
2. Locate high-risk clusters (nodes rendered in Orange / Red).
3. Click on a suspicious hub node (e.g., `A201` - David Vance Shell Business).
4. Review the **Investigation Panel**:
   - Risk Score: 85 (Critical)
   - Reason: Circular Wash Trading (Cycle length 3), Elevated PageRank Centrality.
   - Community ID: Syndicate #4.

## Step 4: Money Trail Highlighting
1. Click **Trace Money Trail** on the selected account.
2. Observe the path highlighted across the graph: `A201 -> A202 -> A203 -> A201`.
3. Inspect edge transaction amounts ($9,900 USD, $9,850 USD, $9,800 USD) showing rapid pass-through structuring.

## Step 5: Triggering Simulated Syndicate Freeze
1. Click the prominent **Freeze Syndicate** button.
2. Confirm the modal: "Apply Simulated Compliance Hold on Syndicate #4 (3 Accounts)".
3. Verify immediate UI feedback:
   - Node status switches to **Frozen** (Ice badge).
   - Alert feed acknowledges action.
   - Navigation to **Audit Log** displays the immutable record: `ACTION: FREEZE_SYNDICATE, TARGET: Community #4, ANALYST: Lead Investigator`.
