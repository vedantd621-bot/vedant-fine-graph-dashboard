# FinGraph Cypher Query Performance Benchmarks

## 1. SLA Objectives
- **Target SLA for Multi-Hop Cypher Queries**: $< 100\text{ ms}$ (p95 execution time)

## 2. Tested Cypher Query Profiles

### Query 1: Direct Transfer Lookup
```cypher
MATCH (a:Account {account_id: $from_id})-[r:TRANSFERRED_TO]->(b:Account {account_id: $to_id})
RETURN a, r, b;
```

### Query 2: Circular Loop Path Detection ($k=2..5$)
```cypher
MATCH path = (a:Account {account_id: $account_id})-[:TRANSFERRED_TO*2..5]->(a)
RETURN [node IN nodes(path) | node.account_id] AS cycle, length(path) AS depth;
```

### Query 3: Multi-Source Funnel Aggregation
```cypher
MATCH (src:Account)-[r1:TRANSFERRED_TO]->(mule:Account)-[r2:TRANSFERRED_TO]->(dst:Account)
WHERE src <> dst AND src <> mule AND mule <> dst
WITH mule, dst, count(DISTINCT src) AS sources, sum(r1.amount) AS total_in
WHERE sources >= 3
RETURN mule.account_id, dst.account_id, sources, total_in;
```

## 3. Empirical Results Matrix (Phase 12 Placeholder)
| Query Name | Graph Size (Nodes/Edges) | Executions | Mean (ms) | p50 (ms) | p95 (ms) | Max (ms) | Target Met? |
|---|---|---|---|---|---|---|---|
| Direct Transfer | 5,000 / 20,000 | 1,000 | TBD | TBD | TBD | TBD | ⏱️ Pending Phase 12 |
| Circular Loop | 5,000 / 20,000 | 1,000 | TBD | TBD | TBD | TBD | ⏱️ Pending Phase 12 |
| Funnel Aggregation | 5,000 / 20,000 | 1,000 | TBD | TBD | TBD | TBD | ⏱️ Pending Phase 12 |
| 3-Hop Money Trail | 5,000 / 20,000 | 1,000 | TBD | TBD | TBD | TBD | ⏱️ Pending Phase 12 |
