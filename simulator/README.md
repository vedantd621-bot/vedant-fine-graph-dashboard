# FinGraph Synthetic Transaction Simulator

The simulator module generates realistic financial transactions mimicking retail, commercial, and adversarial fraud topologies.

## Fraud Scenarios Modeled
1. **Pattern A — Funnel / Smurfing**: Many-to-one aggregation accounts ($A_1..A_n \to I \to B$).
2. **Pattern B — One-to-Many Distribution**: Rapid dispersion from high-value nodes.
3. **Pattern C — Intermediary Chain**: Layered transfers over multiple hops ($A \to B \to C \to D \to E$).
4. **Pattern D — Circular Flow**: Wash-trading loops ($A \to B \to C \to A$).
5. **Pattern E — Layered Network**: Multi-tier aggregation and distribution.

## CLI Usage (Phase 2 preview)
```bash
python src/simulator.py --rate 10 --accounts 200 --suspicious-rate 0.20 --duration 60
```
