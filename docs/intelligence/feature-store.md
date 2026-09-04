# FinGraph ML-Ready Feature Store & Generation

## 1. Feature Store Catalog (18 Normalized Signals)

| Feature Name | Data Type | Source Module | Description |
| :--- | :--- | :--- | :--- |
| `transaction_count_1h` | `float` | Transactions | Transaction count in trailing 1-hour window |
| `transaction_count_24h` | `float` | Transactions | Transaction count in trailing 24-hour window |
| `transaction_volume_24h` | `float` | Transactions | Aggregated transaction volume in trailing 24 hours |
| `avg_transaction_amount` | `float` | Transactions | Mean transaction amount |
| `max_transaction_amount` | `float` | Transactions | Peak single transaction amount |
| `unique_counterparties` | `float` | Topology | Count of distinct connected counterparties |
| `incoming_ratio` | `float` | Transactions | Ratio of incoming volume to total volume |
| `outgoing_ratio` | `float` | Transactions | Ratio of outgoing volume to total volume |
| `pagerank` | `float` | GDS Centrality | Neo4j GDS PageRank centrality score |
| `total_degree` | `float` | Topology | Direct degree connectivity in transaction graph |
| `in_degree` | `float` | Topology | Inbound transfer degree connectivity |
| `out_degree` | `float` | Topology | Outbound transfer degree connectivity |
| `community_size` | `float` | GDS Community | Size of Louvain community cluster |
| `detector_hit_count` | `float` | Detection Engine | Count of matched Cypher fraud detection rules |
| `high_risk_neighbor_count` | `float` | Analytics | Number of counterparties with risk score $\ge 60.0$ |
| `alert_count` | `float` | Alerting | Total active fraud alerts involving this account |
| `is_frozen` | `float` | Compliance | Binary flag (1.0 or 0.0) indicating account freeze |
| `risk_score` | `float` | Risk Engine | Composite graph risk score ($0.0 - 100.0$) |

---

## 2. Batch Export API (`POST /api/v1/features/export`)
Supports on-demand batch export to CSV and JSON formats:
```json
{
  "format": "csv",
  "min_risk_score": 60.0,
  "feature_version": "v1"
}
```
