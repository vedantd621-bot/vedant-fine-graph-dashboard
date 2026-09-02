# FinGraph Synthetic Transaction Simulator

The simulator module generates realistic financial transactions mimicking retail, commercial, and adversarial fraud topologies using **Pydantic V2** and deterministic random seeding.

## Supported Entities
- **Bank**: `bank_id`, `name`, `country`, `routing_number`
- **Person**: `person_id`, `name`, `email`, `country`, `created_at`
- **Account**: `account_id`, `account_type` (`checking`, `savings`, `business`, `shell_business`, `offshore`, `intermediary`), `owner_person_id`, `bank_id`, `risk_score`, `is_frozen`

## Topologies & Scenarios Modeled
1. **Normal Commercial/Retail (`SC_NORMAL`)**:
   - Salary disbursements (wire, \$2,500 – \$9,500)
   - Merchant retail purchases (POS/online, \$8.50 – \$450)
   - Peer-to-peer transfers (mobile, \$20 – \$750)
   - Recurring bills & utilities (online, \$60 – \$1,800)
2. **Pattern A — Funnel / Smurfing (`SC_FUNNEL_01`)**: Multiple accounts send structured sub-\$10k amounts to an intermediary mule account, which sweeps the aggregated sum to an offshore beneficiary.
3. **Pattern B — One-to-Many Distribution (`SC_DISTRIB_01`)**: Single origin account rapidly disburses payments across multiple accounts.
4. **Pattern C — Intermediary Chain (`SC_CHAIN_01`)**: Multi-hop pass-through transfers ($A \to B \to C \to D \to E$) with intermediary fee decay.
5. **Pattern D — Circular Flow (`SC_CIRCULAR_01`)**: Closed-loop round-tripping of funds ($A \to B \to C \to A$) simulating wash-trading volume.
6. **Pattern E — Layered Network (`SC_LAYERED_01`)**: Multi-tier fan-in $\to$ consolidation $\to$ fan-out distribution.

## CLI Usage

### Continuous Real-Time Stream
```bash
python simulator/src/simulator.py --rate 20 --suspicious-rate 0.25 --duration 60
```

### Specific Isolated Fraud Scenario
```bash
python simulator/src/simulator.py --scenario SC_CIRCULAR_01
```

### Emit All Topologies to File
```bash
python simulator/src/simulator.py --scenario all_scenarios --output file:scratch/test_scenarios.jsonl
```

### Command Line Arguments
| Flag | Type | Default | Description |
|---|---|---|---|
| `--rate` | float | `10.0` | Target transactions per second (TPS) |
| `--accounts` | int | `200` | Size of account pool |
| `--people` | int | `150` | Size of entity/person pool |
| `--banks` | int | `10` | Number of banks |
| `--suspicious-rate`| float | `0.20` | Fraction of transactions generated from fraud topologies |
| `--scenario` | str | `stream` | `stream`, `SC_NORMAL`, `SC_FUNNEL_01`, `SC_DISTRIB_01`, `SC_CHAIN_01`, `SC_CIRCULAR_01`, `SC_LAYERED_01`, `all_scenarios` |
| `--duration` | int | `10` | Seconds to stream (`0` for continuous) |
| `--output` | str | `stdout` | `stdout` or `file:<filepath>` |
| `--seed` | int | `42` | Random seed for deterministic reproduction |
| `--quiet` | flag | `False`| Suppress per-event stdout printing |

## Running Tests
```bash
python -m pytest simulator/tests/ -v
```
