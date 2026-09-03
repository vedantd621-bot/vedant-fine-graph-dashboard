# FinGraph Apache Flink Streaming Pipeline Architecture

## 1. Stream Ingestion Pipeline

```
+-----------------------------------------------------------------------------------------+
|                                    FinGraph Simulator                                   |
| (Normal: Salary, Purchases, Bills, Transfers | Fraud: Smurfing, Cycles, Layering, Fans) |
+-----------------------------------------------------------------------------------------+
                                             │
                                             │ (JSON TransactionEvent)
                                             ▼
                             +-------------------------------+
                             |         Apache Kafka          |
                             |      Topic: transactions      |
                             +-------------------------------+
                                             │
                                             │ (Consumer Group: fingraph-flink)
                                             ▼
                             +-------------------------------+
                             |     Apache Flink Pipeline     |
                             |        (flink/src/job.py)     |
                             +-------------------------------+
                                             │
                                             ├── 1. UTF-8 Decode & JSON Parse
                                             ├── 2. Schema Validation (types, amounts, currency)
                                             ├── 3. UTC Timestamp Normalization
                                             │
                                            / \
                         [Valid Transaction]   [Validation Failed / Corrupted]
                                           /     \
                                          v       v
            +--------------------------------+   +--------------------------------+
            |      Neo4j Streaming Sink      |   |        Kafka DLQ Sink          |
            |    (Micro-batched Cypher)      |   |   Topic: 'transactions_dlq'    |
            +--------------------------------+   +--------------------------------+
                           │
                           │ Parameterized Idempotent UNWIND MERGE
                           ▼
            +--------------------------------+
            |     Neo4j Graph Database       |
            | (:Account)-[:TRANSFERRED_TO]-> |
            +--------------------------------+
```

---

## 2. Validation & Normalization Rules

Each transaction is passed through `decode_and_validate`:
1. **UTF-8 and JSON Syntax**: Any decode failure or invalid JSON produces a `DLQEvent`.
2. **Transaction ID**: Must be non-empty string.
3. **Accounts**: `from_account` and `to_account` must be non-empty strings.
4. **Amount**: Numeric, strictly $> 0.0$.
5. **Currency**: Must belong to `VALID_CURRENCIES` (`USD`, `EUR`, `GBP`, `CAD`, `AUD`, `CHF`, `JPY`, `SGD`).
6. **Timestamp**: ISO 8601 parsed and converted to timezone-aware UTC datetime.
7. **Scenario ID**: Normalized string (defaults to `SC_NORMAL`).

---

## 3. Dead Letter Queue (DLQ)

Invalid messages are routed to Kafka topic `transactions_dlq` with payload:
```json
{
  "raw_payload": "{...}",
  "error_reason": "Amount must be strictly positive, got: -500.0",
  "timestamp": "2026-09-03T10:30:00+00:00",
  "source_topic": "transactions",
  "partition": 0,
  "offset": 42
}
```

---

## 4. Neo4j Batch Ingestion & Idempotency

The `Neo4jStreamingSink` buffers records into batches (`NEO4J_SINK_BATCH_SIZE=50`) or flushes on interval (`NEO4J_SINK_FLUSH_INTERVAL_MS=1000`).
The Cypher write query uses `UNWIND $batch AS event` with `MERGE` on `Account` and `MERGE (src)-[r:TRANSFERRED_TO {transaction_id: event.transaction_id}]->(dst)`.
- If an event is re-delivered (duplicate), it updates properties without creating redundant relationships or duplicate nodes.
