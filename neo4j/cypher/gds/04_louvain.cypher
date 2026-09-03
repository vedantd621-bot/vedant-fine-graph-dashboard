// =============================================================================
// FinGraph GDS Cypher: Louvain Community Detection
// =============================================================================

CALL gds.louvain.mutate($graph_name, {
    mutateProperty: 'louvain_community_id',
    relationshipWeightProperty: 'amount'
})
YIELD communityCount, modularity, modularities;

CALL gds.graph.nodeProperties.write($graph_name, ['louvain_community_id'])
YIELD propertiesWritten
RETURN propertiesWritten;
