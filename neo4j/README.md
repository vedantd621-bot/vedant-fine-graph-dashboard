# FinGraph Neo4j Graph Database & Analytics

Contains all Cypher migration scripts, node uniqueness constraints, performance indexes, fraud query library, Graph Data Science (GDS) projection procedures, and baseline seed data.

## Directory Structure
- `constraints/`: Uniqueness constraints for `Person`, `Account`, `Bank`, and `Transaction`.
- `indexes/`: Composite, range, and lookup indexes for sub-100ms multi-hop traversal.
- `cypher/`: Parameterized queries for detecting cycles, funnels, distribution fans, and money trails.
- `gds/`: Graph Data Science algorithm executions (Louvain Community, PageRank, WCC).
- `seed/`: Deterministic synthetic graph seed for testing and local bootstrapping.
