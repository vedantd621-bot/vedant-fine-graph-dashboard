# FinGraph Apache Flink Streaming Pipeline

The Flink module implements the real-time stream ingestion, validation, normalization, dead-letter routing, and batched Neo4j graph persistence.

---

## 1. Architecture Overview
- `src/config.py`: Environment configuration for Kafka, DLQ, Neo4j, and Flink runtime.
- `src/schemas.py`: Canonical transaction models and `DLQEvent` structures.
- `src/transforms.py`: UTF-8 decoding, JSON parsing, schema validation, and UTC normalization.
- `src/neo4j_sink.py`: Parameterized micro-batched Neo4j Cypher sink with idempotency.
- `src/dlq_sink.py`: Dead Letter Queue sink publishing corrupted records to `transactions_dlq`.
- `src/metrics.py`: Real-time streaming metrics (received, valid, written, DLQ, failed).
- `src/job.py`: Main streaming pipeline runner.

---

## 2. Running the Pipeline

### Dry Run (Validation Mode)
```bash
python flink/src/job.py --dry-run
```

### Run Live Consumer Loop
```bash
python flink/src/job.py --bootstrap-servers localhost:9092 --topic transactions
```

---

## 3. Running Tests
```bash
python -m pytest tests/flink/ -v
```
