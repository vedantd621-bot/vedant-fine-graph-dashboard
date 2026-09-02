// =============================================================================
// FinGraph: Graph Data Science (GDS) Graph Projections & Algorithms
// =============================================================================

// 1. Drop existing in-memory graph projection if exists
CALL gds.graph.drop('fingraph-network', false) YIELD graphName;

// 2. Project In-Memory Graph (Account nodes & TRANSFERRED_TO edges with weights)
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

// 3. PageRank Centrality Computation (Stream or Mutate)
CALL gds.pageRank.mutate('fingraph-network', {
    mutateProperty: 'pagerank',
    dampingFactor: 0.85,
    maxIterations: 20
})
YIELD nodePropertiesWritten, computeMillis;

// 4. Louvain Community Detection (Identify tightly knit fraud syndicates)
CALL gds.louvain.mutate('fingraph-network', {
    mutateProperty: 'community_id',
    includeIntermediateCommunities: false,
    relationshipWeightProperty: 'amount'
})
YIELD communityCount, modularity, modularities;

// 5. Weakly Connected Components (WCC)
CALL gds.wcc.mutate('fingraph-network', {
    mutateProperty: 'wcc_component_id'
})
YIELD componentCount, computeMillis;

// 6. Write back computed graph metrics to Neo4j persistence store
CALL gds.graph.nodeProperties.write('fingraph-network', ['pagerank', 'community_id', 'wcc_component_id'])
YIELD propertiesWritten;
