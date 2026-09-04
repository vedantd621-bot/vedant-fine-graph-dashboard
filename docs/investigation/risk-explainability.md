# Explainable Risk Scoring & Intelligence

## Formulation & Factor Weights

FinGraph computes an explainable multi-dimensional risk score for entities by combining rule-based detector signals with topological GDS metrics:

$$\text{Risk Score} = \min\left(100.0, \sum_{i} w_i \cdot s_i + \text{GDS Centrality Bonus} + \text{Community Penalty}\right)$$

### Factor Catalog & Weights

| Factor Code | Description | Severity | Base Weight ($w_i$) | Evidence Reference |
| :--- | :--- | :--- | :--- | :--- |
| **`DETECTOR_CIRCULAR_FLOW`** | Closed loop fund cycling topology | CRITICAL | 3.5 | Cycle path nodes & amounts |
| **`DETECTOR_FUNNEL`** | High fan-in rapid consolidation | HIGH / CRITICAL | 3.5 | Inflow ratio & source count |
| **`DETECTOR_ONE_TO_MANY`** | Rapid fan-out mule dispersion | HIGH | 2.5 | Outflow ratio & target count |
| **`DETECTOR_CHAIN`** | Multi-hop rapid relay laundering | HIGH | 2.5 | Hop depth & velocity |
| **`HIGH_PAGERANK_CENTRALITY`** | Elevated network flow transit ($PR \ge 0.5$) | HIGH | 2.0 | GDS PageRank score |
| **`HIGH_CONNECTIVITY_DEGREE`** | Extreme counterparty degree ($k \ge 5$) | MEDIUM | 1.5 | Direct node degree |
| **`BASELINE_ACTIVITY`** | Normal consumer retail volume | LOW | 0.5 | Baseline risk rating |

---

## Actionable Next-Step Recommendations

When an alert is flagged, the intelligence service analyzes the graph structure to recommend concrete operations:

1. **`INSPECT_TRAIL`**: Triggered on `CIRCULAR_FLOW`, `CHAIN`, and `FUNNEL` alerts to trace multi-hop exit mules.
2. **`FREEZE_ACCOUNT`**: Recommended when focal entity risk score $\ge 85.0$ or alert severity is `CRITICAL`.
3. **`CREATE_CASE`**: Suggested for complex syndicates involving $>3$ interconnected accounts.
4. **`REVIEW_COUNTERPARTIES`**: Advised when high fan-out or shared community clusters are detected.
