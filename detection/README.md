# FinGraph Cypher Fraud Detection & Investigation Engine

The Detection module provides high-performance graph pattern detection algorithms executing directly in Neo4j using parameterized Cypher.

---

## 1. Supported Detectors
- **Funnel / Smurfing**: Aggregations into intermediary mules with exit sweeps.
- **One-to-Many Distribution**: Rapid dispersion from a single source to multiple destinations.
- **Intermediary Chain**: Linear pass-through sequences ($A \to B \to C \to D$).
- **Circular Flow**: Closed-loop wash trading cycles ($A \to B \to C \to A$) with canonical rotational deduplication.
- **Layered Network**: 4-tier syndicates (Sources $\to$ Intermediaries $\to$ Aggregator $\to$ Exits).
- **High-Degree Hubs**: Unusually connected accounts.
- **Money Trail**: Forensic multi-hop path tracing.

---

## 2. CLI Usage

### Run All Detectors (Formatted Report)
```bash
python -m detection.src.cli --all
```

### Run Specific Detectors with Custom Thresholds
```bash
python -m detection.src.cli --funnel --min-sources 4
python -m detection.src.cli --circular --min-length 3
python -m detection.src.cli --chain --min-depth 4
```

### Trace Multi-Hop Money Trail
```bash
python -m detection.src.cli --money-trail --from-account A001 --to-account A006
```

### JSON Output Mode
```bash
python -m detection.src.cli --all --format json
```

### Dry Run / Offline Validation Mode
```bash
python -m detection.src.cli --dry-run
```

---

## 3. Running Tests
```bash
python -m pytest tests/detection/ -v
```
