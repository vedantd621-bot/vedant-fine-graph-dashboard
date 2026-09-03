# FinGraph GDS Analytics & Explainable Risk Scoring Engine

The Analytics module provides Graph Data Science (GDS) algorithms and a transparent, explainable account risk scoring engine.

---

## 1. Features
- **In-Memory GDS Projection**: Manages graph projection `fingraph` on `Account` nodes and `TRANSFERRED_TO` relationships.
- **PageRank Centrality**: Identifies high-velocity routing nodes and liquidity hubs.
- **Weakly Connected Components (WCC)**: Partitions network into connected transaction islands.
- **Louvain Modularity**: Detects tightly knit syndicate clusters.
- **Explainable Risk Scoring**: Blends 60% rule-based detections + 40% GDS graph metrics into a calibrated 0–100 score with human-readable rationale.

---

## 2. CLI Usage

### Run Complete Analytics & Risk Scoring Pipeline
```bash
python -m analytics.src.cli --all
```

### Inspect Single Account
```bash
python -m analytics.src.cli --account A005
```

### GDS Projection Management
```bash
python -m analytics.src.cli --create-projection
python -m analytics.src.cli --run-gds
python -m analytics.src.cli --drop-projection
```

### Persist Risk Scores into Neo4j
```bash
python -m analytics.src.cli --calculate-risk --persist
```

### JSON Format Output
```bash
python -m analytics.src.cli --account A005 --format json
```

### Offline / Dry Run Validation
```bash
python -m analytics.src.cli --dry-run
```

---

## 3. Running Tests
```bash
python -m pytest tests/analytics/ -v
```
