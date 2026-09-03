# FinGraph Explainable Risk Scoring Framework

## 1. Methodology & Philosophy
The FinGraph Risk Engine blends symbolic graph pattern detections (Phase 6) with topological GDS metrics (Phase 7) into a transparent, deterministic 0–100 risk score for every bank account.

```
+------------------------------------+        +------------------------------------+
|       Phase 6 Rule Subscore        |        |       Phase 7 Graph Subscore       |
|    - Funnel / Smurfing (+25)       |        |    - PageRank Centrality (40%)     |
|    - Circular Wash Trading (+30)   |        |    - Total Node Degree (30%)       |
|    - Layered Syndicate (+30)       |        |    - Community Cluster Risk (30%)  |
|    - One-to-Many Dispersion (+15)  |        |                                    |
|    - Intermediary Chain (+15)      |        |                                    |
|    - High-Degree Hub (+10)         |        |                                    |
|           (Scale: 0 - 100)         |        |          (Scale: 0 - 100)          |
+------------------------------------+        +------------------------------------+
                  │                                              │
                  ▼ (Weight: 60%)                                ▼ (Weight: 40%)
       +─────────────────────────────────────────────────────────────────+
       |       Composite Risk Score = (Rule * 0.60) + (Graph * 0.40)      |
       +─────────────────────────────────────────────────────────────────+
                                         │
                                         ▼
       +─────────────────────────────────────────────────────────────────+
       |      Categorical Risk Bands & Human-Readable Audit Reasons      |
       |  - 0.00 – 24.99:  LOW                                           |
       |  - 25.00 – 49.99: MEDIUM                                        |
       |  - 50.00 – 74.99: HIGH                                          |
       |  - 75.00 – 100.0: CRITICAL                                      |
       +─────────────────────────────────────────────────────────────────+
```

---

## 2. Formal Mathematical Formula

$$\text{Rule Subscore} = \min\left(100.0, \sum_{i \in \text{active patterns}} \text{Points}_i\right)$$

$$\text{Graph Subscore} = \min\left(100.0, (\text{NormPR} \times 0.40) + (\text{NormDegree} \times 0.30) + (\text{NormComm} \times 0.30)\right)$$

$$\text{Final Risk Score} = (\text{Rule Subscore} \times 0.60) + (\text{Graph Subscore} \times 0.40)$$

---

## 3. Explainability & Justification
Every evaluated account receives an audit trail of clear justifications, for example:
- *Account functions as an intermediary aggregation mule in a structured funneling pattern.*
- *Account participates in a closed circular wash-trading loop.*
- *Elevated PageRank centrality (0.582) identifies account as a structural liquidity transit hub.*
- *Belongs to a dense transaction community cluster of 6 accounts.*

---

## 4. Compliance Notice & Disclaimer
> [!IMPORTANT]
> The calculated risk score is an explainable rule-and-graph signal for investigation prioritization. It is not proof of fraud and is not a legally validated fraud determination.
