# FinGraph Streaming Ingestion Latency Report

## 1. Metric Definition
The streaming ingestion latency measures the total elapsed time between when a synthetic transaction event is minted by the generator (`event_created_at`) and when the corresponding node/edge becomes queryable inside Neo4j (`graph_visible_at`):

$$
\text{Latency (ms)} = T_{\text{Neo4j Visible}} - T_{\text{Event Created}}
$$

## 2. SLA Objective
- **Target SLA**: $< 1,000\text{ ms}$ (Sub-second real-time detection)

## 3. Benchmark Methodology
- Inject continuous batches of transactions at rates varying from $10\text{ tx/s}$ to $1,000\text{ tx/s}$.
- Sample transaction IDs and verify timestamp deltas.
- Aggregate metrics: Mean, Median (p50), 95th Percentile (p95), 99th Percentile (p99), Max.

## 4. Benchmark Measurement Log (Phase 12 Placeholder)
| Ingestion Rate | Mean Latency | Median (p50) | p95 Latency | p99 Latency | Status |
|---|---|---|---|---|---|
| 10 tx/sec | TBD | TBD | TBD | TBD | Pending Phase 12 |
| 100 tx/sec | TBD | TBD | TBD | TBD | Pending Phase 12 |
| 500 tx/sec | TBD | TBD | TBD | TBD | Pending Phase 12 |
| 1000 tx/sec | TBD | TBD | TBD | TBD | Pending Phase 12 |
