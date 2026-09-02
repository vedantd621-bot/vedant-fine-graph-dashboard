# FinGraph Synthetic Transaction Simulator & Kafka Streaming Integration

The simulator module generates realistic financial transactions mimicking retail, commercial, and adversarial fraud topologies using **Pydantic V2** and streams them to **Apache Kafka** with decoupled output sink abstractions.

---

## 1. Supported Entities
- **Bank**: `bank_id`, `name`, `country`, `routing_number`
- **Person**: `person_id`, `name`, `email`, `country`, `created_at`
- **Account**: `account_id`, `account_type` (`checking`, `savings`, `business`, `shell_business`, `offshore`, `intermediary`), `owner_person_id`, `bank_id`, `risk_score`, `is_frozen`

---

## 2. Topologies & Scenarios Modeled
1. **Normal Commercial/Retail (`SC_NORMAL`)**:
   - Salary disbursements (Wire, \$2,500 – \$9,500)
   - Merchant retail purchases (POS/online, \$8.50 – \$450)
   - Peer-to-peer transfers (Mobile, \$20 – \$750)
   - Recurring bills & utilities (Online, \$60 – \$1,800)
2. **Pattern A — Funnel / Smurfing (`SC_FUNNEL_01`)**: Multiple accounts send structured sub-\$10k amounts to an intermediary mule account, which sweeps the aggregated sum to an offshore beneficiary.
3. **Pattern B — One-to-Many Distribution (`SC_DISTRIB_01`)**: Single origin account rapidly disburses payments across multiple accounts.
4. **Pattern C — Intermediary Chain (`SC_CHAIN_01`)**: Multi-hop pass-through transfers ($A \to B \to C \to D \to E$) with intermediary fee decay.
5. **Pattern D — Circular Flow (`SC_CIRCULAR_01`)**: Closed-loop round-tripping of funds ($A \to B \to C \to A$) simulating wash-trading volume.
6. **Pattern E — Layered Network (`SC_LAYERED_01`)**: Multi-tier fan-in $\to$ consolidation $\to$ fan-out distribution.

---

## 3. Architecture & Output Sinks

Events flow from the generator through a pluggable output sink abstraction:

```
+---------------------+        +--------------------+
|  FinGraphGenerator  |------->|  TransactionEvent  |
+---------------------+        +--------------------+
                                         │
                                         ▼
                               +--------------------+
                               | create_output_sink |
                               +--------------------+
                                 /        │         \
                                /         │          \
                               v          v           v
                          StdoutSink   FileSink   KafkaSink
                                                      │
                                                      ▼
                                            KafkaTopic ('transactions')
                                            - Key: transaction_id
                                            - Acks: all
                                            - Retry & Exponential Backoff
```

---

## 4. Apache Kafka Configuration

Kafka settings are loaded via environment variables (`.env`):

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker host and port |
| `KAFKA_TOPIC` | `transactions` | Target topic for raw transaction events |
| `KAFKA_CLIENT_ID` | `fingraph-simulator` | Producer client identifier |
| `KAFKA_ACKS` | `all` | Delivery guarantee level (`all` / `-1`) |
| `KAFKA_RETRIES` | `5` | Connection retry attempts on startup |
| `KAFKA_RETRY_BACKOFF_MS` | `500` | Initial exponential backoff delay in ms |

---

## 5. CLI Usage Examples

### Publish Transactions to Kafka
```bash
python simulator/src/simulator.py --rate 15 --suspicious-rate 0.25 --duration 30 --output kafka
```

### Emit Specific Fraud Scenario to Kafka
```bash
python simulator/src/simulator.py --scenario SC_CIRCULAR_01 --output kafka
```

### Stream to Standard Output (Stdout)
```bash
python simulator/src/simulator.py --rate 10 --suspicious-rate 0.20 --duration 10 --output stdout
```

### Export to JSON-Lines File
```bash
python simulator/src/simulator.py --scenario all_scenarios --output file:scratch/scenarios.jsonl
```

---

## 6. Kafka Debug Consumer CLI

Inspect and validate live events flowing through the `transactions` topic:

```bash
# Read live incoming stream
python simulator/src/consumer.py

# Consume all messages from earliest offset
python simulator/src/consumer.py --from-beginning

# Specify custom broker or topic
python simulator/src/consumer.py --bootstrap-servers localhost:9092 --topic transactions --timeout 30
```

---

## 7. Running Tests
```bash
# Run simulator and Kafka producer/consumer unit tests
python -m pytest simulator/tests/ -v

# Run full suite including end-to-end integration contracts
python -m pytest simulator/tests/ tests/integration/ -v
```
