# FinGraph Apache Flink Streaming Pipeline

The Flink module processes streaming transaction events from Kafka, performs schema validation, timestamp/amount normalization, rejects malformed payloads safely, computes stateful temporal window aggregations, and batches graph upserts to Neo4j.

## Pipeline Flow
```
Kafka Topic ("transactions")
    │
    ▼
JSON Deserialization & Validation
    │
    ├── Malformed ──► Dead Letter / Log
    │
    ▼ Validated
Data Cleaning & Normalization
    │
    ▼
Stateful Anomaly & Velocity Enrichment
    │
    ▼
Batched Sink to Neo4j
```
