# FinGraph Neo4j Graph Data Science (GDS) Architecture

## 1. Overview
FinGraph integrates the Neo4j Graph Data Science (GDS 2.x) library to execute graph-native centrality, partitioning, and community detection algorithms over the transaction topology.

```
       +-----------------------------------------------------------+
       |             Neo4j Operational Graph Database              |
       |       (:Account)-[:TRANSFERRED_TO {amount, ts}]->         |
       +-----------------------------------------------------------+
                                     │
                                     ▼  CALL gds.graph.project()
       +-----------------------------------------------------------+
       |         In-Memory Analytical Graph: 'fingraph'            |
       |            Node: Account | Rel: TRANSFERRED_TO            |
       |               Relationship Property: amount               |
       +-----------------------------------------------------------+
                    │                │                │
                    ▼                ▼                ▼
             +-------------+  +-------------+  +-------------+
             |  PageRank   |  |     WCC     |  |   Louvain   |
             | Centrality  |  | Components  |  | Communities |
             +-------------+  +-------------+  +-------------+
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                                     ▼  CALL gds.graph.nodeProperties.write()
       +-----------------------------------------------------------+
       |     Persisted Account Properties in Neo4j Graph           |
       |  - pagerank_score                                         |
       |  - wcc_id                                                 |
       |  - louvain_community_id                                   |
       +-----------------------------------------------------------+
```

---

## 2. In-Memory Graph Projection (`fingraph`)
The analytical graph is projected from the operational database using:
```cypher
CALL gds.graph.project(
    'fingraph',
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

---

## 3. Algorithms & Metrics

### 1. PageRank Centrality (`gds.pageRank.mutate`)
- **Purpose**: Measures structural importance and liquidity transit volume through accounts.
- **Parameters**: `dampingFactor: 0.85`, `maxIterations: 20`.
- **Interpretation**: Higher PageRank identifies intermediary aggregation pools, mule brokers, and high-velocity routing nodes.

### 2. Weakly Connected Components (`gds.wcc.mutate`)
- **Purpose**: Partitions the graph into isolated, disjoint transaction islands and components.
- **Interpretation**: Isolates closed syndicate rings and syndicates operating independently from main retail banking flows.

### 3. Louvain Community Modularity (`gds.louvain.mutate`)
- **Purpose**: Identifies tightly-knit clusters of accounts with unusually high internal transaction density.
- **Parameters**: Weighted by transaction `amount`.
- **Interpretation**: Uncovers syndicate cells where funds cycle frequently within an insular group of accounts.

---

## 4. Compliance & Interpretability Notice
> [!NOTE]
> GDS graph algorithms produce topological features and structural signals for investigation prioritization. High PageRank or dense community membership does **not** constitute proof of criminal misconduct.
