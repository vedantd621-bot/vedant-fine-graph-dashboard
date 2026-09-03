# FinGraph Neo4j Graph Database Architecture

## 1. Graph Model Design

FinGraph implements a property graph model optimized for real-time stream ingestion and sub-100ms multi-hop traversal.

```
       +------------------+
       |     (Person)     |
       | - person_id (PK) |
       | - name           |
       | - country        |
       +------------------+
                 │
                 │ OWNS
                 ▼
       +------------------+                    +------------------+
       |    (Account)     |                    |      (Bank)      |
       | - account_id (PK)|─── HOSTED_BY ─────>| - bank_id (PK)   |
       | - account_type   |                    | - name           |
       | - risk_score     |                    | - country        |
       | - is_frozen      |                    +------------------+
       +------------------+
          │            ▲
          │            │
          │ TRANSFERRED_TO
          │ (transaction_id, amount, currency, timestamp, scenario_id)
          └────────────┘
```

### Why Relationship Properties on `TRANSFERRED_TO`?
1. **Traversability**: Path traversal algorithms ($A \to B \to C \to D$) traverse direct edges without requiring intermediate node hops ($A \to T_1 \to B \to T_2 \to C$).
2. **Neo4j Graph Data Science (GDS) Alignment**: Native GDS graph projections project directed relationships between accounts with relationship property weights (`amount`).
3. **Indexable & Fast**: Direct filtering on relationship properties (`r.timestamp`, `r.scenario_id`, `r.transaction_id`).

---

## 2. Uniqueness Constraints & Performance Indexes

### Uniqueness Constraints
- `c_account_id_unique`: `FOR (a:Account) REQUIRE a.account_id IS UNIQUE`
- `c_person_id_unique`: `FOR (p:Person) REQUIRE p.person_id IS UNIQUE`
- `c_bank_id_unique`: `FOR (b:Bank) REQUIRE b.bank_id IS UNIQUE`

### Indexes
- `idx_account_risk_score`: Range index on `Account.risk_score`
- `idx_account_community_id`: Index on `Account.community_id`
- `idx_person_name`: Index on `Person.name`
- `idx_rel_transferred_timestamp`: Relationship index on `TRANSFERRED_TO.timestamp`
- `idx_rel_transferred_scenario`: Relationship index on `TRANSFERRED_TO.scenario_id`
- `idx_rel_transferred_tx_id`: Relationship index on `TRANSFERRED_TO.transaction_id`

---

## 3. Deterministic Seed Data Topologies

The baseline seed dataset in `neo4j/seed/seed_data.py` populates:
- **4 Banks**: `B01` (Apex Global Bank), `B02` (Horizon Trust Bank), `B03` (Pinnacle Credit Union), `B04` (Sterling Standard Bank).
- **25 People**: `P001` to `P025`.
- **30 Accounts**: `A001` to `A030`.
- **26 Transactions**:
  - `SC_NORMAL`: Salary, retail purchases, peer transfers, utility payments.
  - `SC_FUNNEL_01`: `A001`, `A002`, `A003`, `A004` (structured inflows) $\to$ `A005` (Intermediary Mule) $\to$ `A006` (Offshore exit).
  - `SC_DISTRIB_01`: `A010` (Source) $\to$ `A011`, `A012`, `A013`, `A014`, `A015`.
  - `SC_CHAIN_01`: `A020` $\to$ `A021` $\to$ `A022` $\to$ `A023` $\to$ `A024`.
  - `SC_CIRCULAR_01`: `A025` $\to$ `A026` $\to$ `A027` $\to$ `A025`.
  - `SC_LAYERED_01`: `A028`, `A029` $\to$ `A016`, `A017` $\to$ `A007` $\to$ `A008`, `A009`.

---

## 4. Graph Data Science (GDS) Preparation (Phase 7 Roadmap)

FinGraph is architected for GDS in-memory graph projections:
```cypher
CALL gds.graph.project(
    'fingraph-network',
    'Account',
    {
        TRANSFERRED_TO: {
            type: 'TRANSFERRED_TO',
            orientation: 'NATURAL',
            properties: ['amount']
        }
    }
);
```

Algorithms to be executed:
- **Louvain Community Detection**: Uncover isolated fraud clusters/syndicates.
- **PageRank Centrality**: Identify key money transit nodes and liquidity aggregators.
- **Weakly Connected Components (WCC)**: Disconnected subgraph partition analysis.
