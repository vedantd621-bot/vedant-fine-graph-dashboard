# FinGraph Synthetic Test Scenarios & Topologies

| Scenario ID | Topology Name | Description | Nodes Involved | Expected Risk Class |
|---|---|---|---|---|
| `SC_NORMAL` | Commercial / Retail | Normal peer-to-peer transfers, salary disbursements, bill payments. | Random pairs | **Low (0–29)** |
| `SC_FUNNEL_01` | Smurfing / Funnel Aggregator | Multiple small accounts deposit into an intermediary mule, which sweeps out to a beneficiary. | $A_1, A_2, A_3 \to I \to B$ | **High (60–79)** |
| `SC_DISTRIB_01` | One-to-Many Dispersion | Single high-value source distributes rapid payments to 10+ destination accounts. | $S \to D_1..D_{10}$ | **High (60–79)** |
| `SC_CHAIN_01` | Intermediary Pass-Through | Money moves through 4+ linear hops without economic justification. | $A \to B \to C \to D \to E$ | **Medium to High (50–70)** |
| `SC_CIRCULAR_01` | Circular Wash Trading | Closed-loop round trip transferring funds back to origin with minor fees deducted. | $A \to B \to C \to A$ | **Critical (80–100)** |
| `SC_LAYERED_01` | Multi-Tier Syndicate | Funneling $\to$ Intermediary Chains $\to$ Distributed Exit Accounts. | 15+ Accounts | **Critical (80–100)** |
