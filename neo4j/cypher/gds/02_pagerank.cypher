// =============================================================================
// FinGraph GDS Cypher: PageRank Centrality Computation
// =============================================================================

// Compute PageRank and write back to Account.pagerank_score
CALL gds.pageRank.mutate($graph_name, {
    mutateProperty: 'pagerank_score',
    dampingFactor: 0.85,
    maxIterations: 20
})
YIELD nodePropertiesWritten, computeMillis;

CALL gds.graph.nodeProperties.write($graph_name, ['pagerank_score'])
YIELD propertiesWritten
RETURN propertiesWritten;
