# FinGraph Neo4j Graph Database & Analytics Foundation

The Neo4j module provides the core graph database foundation, Cypher migration scripts, uniqueness constraints, performance indexes, fraud query library, Graph Data Science (GDS) projection procedures, and deterministic seed infrastructure.

---

## 1. Directory Structure
- `constraints/`: Uniqueness constraints for `Person`, `Account`, and `Bank` entities.
- `indexes/`: Composite, property, and relationship indexes for sub-100ms multi-hop traversal.
- `cypher/`: Parameterized queries for detecting cycles, funnels, distribution fans, and money trails.
- `gds/`: Graph Data Science algorithm execution procedures (Louvain Community, PageRank, WCC).
- `seed/`: Deterministic synthetic graph seed data and Cypher migration script.
- `scripts/`: CLI utilities for schema initialization (`init_schema.py`) and database seeding (`seed.py`).
- `src/`: Reusable Neo4j driver client (`client.py`) and Cypher query wrappers (`queries.py`).

---

## 2. Configuration (`.env`)
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fingraph_secret_pass
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30
```

---

## 3. CLI Operations

### Initialize Schema & Indexes
```bash
python neo4j/scripts/init_schema.py
```

### Seed Database with Deterministic Graph
```bash
python neo4j/scripts/seed.py
```

---

## 4. Running Tests
```bash
python -m pytest tests/neo4j/ -v
```
