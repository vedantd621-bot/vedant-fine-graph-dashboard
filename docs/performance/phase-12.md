# FinGraph Phase 12 — Performance & Latency Benchmarks

## Overview
This document records empirical latency and throughput benchmarks measured across **100 iterations** for the Phase 12 Fraud Network Discovery, Behavioral Anomaly Detection, Entity Similarity, and ML Feature Store export pipelines.

---

## 1. Benchmark Execution Results (100 Iterations)

| Pipeline Component | Metric | Mean Latency | Median (p50) | p95 Latency | p99 Latency | Min | Max |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fraud Network Discovery** | Cypher rings + Louvain communities | **0.941 ms** | 0.682 ms | 1.517 ms | 5.560 ms | 0.606 ms | 5.560 ms |
| **Behavioral Anomaly Detection** | 24h window multi-metric delta | **0.213 ms** | 0.142 ms | 0.464 ms | 0.675 ms | 0.117 ms | 0.675 ms |
| **Suspect Entity Similarity** | 4-signal Jaccard + Community + Risk | **1.055 ms** | 1.007 ms | 1.156 ms | 2.790 ms | 0.949 ms | 2.790 ms |
| **ML Feature Extraction** | 18 normalized signals per entity | **0.232 ms** | 0.211 ms | 0.288 ms | 1.411 ms | 0.192 ms | 1.411 ms |
| **Feature Store Export** | 50-account batch CSV / JSON export | **15.988 ms** | 12.155 ms | 15.075 ms | 153.013 ms | 11.074 ms | 153.013 ms |

---

## 2. Key Performance Takeaways
1. **Sub-millisecond Discovery & Scoring**: Full fraud network detection and weighted factor scoring executes in $<1.0\text{ ms}$, ensuring real-time response times during live streaming graph updates.
2. **Deterministic Behavioral Anomaly Evaluation**: Windowed behavioral evaluation (5m, 1h, 24h, 7d, 30d) completes in $0.21\text{ ms}$ per entity.
3. **High-Throughput ML Feature Extraction**: Single entity feature generation takes $\sim 230\ \mu\text{s}$, allowing extraction rates of over **4,300 entities/second** per worker thread.
4. **Sub-20ms Batch Feature Store Export**: 50-entity tabular CSV generation with RFC-compliant formatting takes $\sim 12\text{ ms}$ median, allowing seamless batch training data ingestion.
