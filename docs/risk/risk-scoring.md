# FinGraph Explainable Risk Scoring Engine

## 1. Principles of Explainable AML Risk

Financial compliance requires full explainability. Black-box ML models are often rejected by regulatory auditors because they cannot explain why an account was flagged. FinGraph uses a deterministic, rule-and-topology-grounded composite formula.

> [!NOTE]
> Risk scores range from **0 to 100** and represent structural suspicion indices, not conclusive evidence of unlawful activity.

---

## 2. Risk Classification Bands

| Score Band | Severity Level | System Response | Analyst Action |
|---|---|---|---|
| **0 – 29** | **Low** | Normal monitoring | None required |
| **30 – 59** | **Medium** | Logged to investigation feed | Standard periodic review |
| **60 – 79** | **High** | High-priority alert triggered | Expedited SAR / Network review |
| **80 – 100** | **Critical** | Critical alert + Freeze Candidate | Immediate containment / Freeze action |

---

## 3. Mathematical Formula

The composite risk score $R(a)$ for account $a$ is calculated as:

$$
R(a) = \min\left(100, \; \sum_{i=1}^5 w_i \cdot S_i(a)\right)
$$

Where the factor signals $S_i(a) \in [0, 100]$ and weights $w_i$ ($\sum w_i = 1.0$) are defined as:

### 1. Connection Degree Centrality ($w_1 = 0.20$)
Measures the number of incoming ($d_{\text{in}}$) and outgoing ($d_{\text{out}}$) counterparties.
$$
S_{\text{degree}}(a) = \min\left(100, \; (d_{\text{in}} + d_{\text{out}}) \times 5\right)
$$

### 2. Circular Flow / Cycle Participation ($w_2 = 0.30$)
Accounts involved in closed-loop cycles ($A \to B \to C \to A$) receive an immediate high-weight penalty.
$$
S_{\text{cycle}}(a) = \begin{cases} 100 & \text{if member of cycle length } \le 5 \\ 0 & \text{otherwise} \end{cases}
$$

### 3. PageRank Centrality ($w_3 = 0.15$)
Identifies critical structural hubs and liquidity conduits in the directed transaction graph.
$$
S_{\text{pagerank}}(a) = \min\left(100, \; \text{PageRank}(a) \times 1000\right)
$$

### 4. Velocity & Funneling Signal ($w_4 = 0.20$)
Detects rapid pass-through or smurfing concentration (ratio of in-flow to out-flow within short temporal windows).
$$
S_{\text{velocity}}(a) = \min\left(100, \; \text{ConcentrationRatio}(a) \times 100\right)
$$

### 5. Louvain Community Syndicate Density ($w_5 = 0.15$)
Penalizes membership in dense, highly clustered subgraphs where the average neighbor risk is elevated.
$$
S_{\text{community}}(a) = \overline{R}(\text{Neighbors of } a)
$$
