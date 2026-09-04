# FinGraph Fraud Network & Collusive Syndicate Discovery

## 1. Discovery Methodology
FinGraph discovers collusive fraud syndicates and laundering rings deterministically using graph topology, Cypher detection fingerprints, and Neo4j GDS community clusters.

### Supported Network Types
- **CIRCULAR_RING**: Closed wash-trading loops (e.g. $A \to B \to C \to A$) with zero net economic displacement.
- **FAN_IN_CONSOLIDATION**: Funnel topologies where multiple mule feeder accounts concentrate capital into a single aggregator node.
- **FAN_OUT_DISPERSION**: Dispersion topologies where a central hub disperses structured funds across multiple mule destination accounts.
- **LAYERED_CHAIN**: Multi-hop intermediary paths designed to obfuscate origin and destination.
- **COMMUNITY_SYNDICATE**: Dense Louvain community clusters exhibiting collective risk $\ge 40.0$.
- **SHARED_INFRASTRUCTURE**: Hub accounts acting as common counterparties across high-risk suspects.

---

## 2. Network-Level Risk Scoring Formula
Network risk scores ($0 - 100$) are calculated via deterministic weighted factor contributions:

$$\text{Network Risk Score} = \sum_{i=1}^5 w_i \times S_i$$

| Factor Name | Weight ($w_i$) | Raw Metric ($S_i$) | Description |
| :--- | :--- | :--- | :--- |
| **High-Risk Member Density** | $0.25$ | $\frac{\text{Members with Risk} \ge 60}{\text{Total Members}} \times 100$ | Proportion of constituent accounts carrying high or critical risk. |
| **Detector Density** | $0.25$ | $\min(100, \text{Detector Matches} \times 25)$ | Frequency of matched Cypher fraud detection rules within the ring. |
| **Volume Concentration** | $0.20$ | $\min(100, \log_{10}(\text{Volume} + 1) \times 20)$ | Aggregated dollar volume circulating through the network. |
| **Topological Structure** | $0.20$ | Ring ($85$), Chain ($75$), Funnel ($70$), Dispersion ($70$), Cluster ($60$) | Intrinsic structural severity of the graph topology. |
| **Community Risk Aggregation** | $0.10$ | Average risk score of member Louvain communities | Macro-cluster risk level in the broader transaction graph. |

---

## 3. Network Member Role Inference
- **ORIGINATOR**: Primary seed account or initial source of funds.
- **AGGREGATOR**: Inbound funnel hub node receiving funds from $\ge 3$ sources.
- **DISPERSER**: Outbound distribution hub node broadcasting funds to $\ge 3$ targets.
- **MULE**: Low-balance, high-throughput intermediary pass-through node.
- **INTERMEDIARY**: Multi-hop path relayer in layered chain structures.
- **MEMBER**: Standard cluster participant within a Louvain community syndicate.
