// =============================================================================
// FinGraph GDS Cypher: Weakly Connected Components (WCC)
// =============================================================================

CALL gds.wcc.mutate($graph_name, {
    mutateProperty: 'wcc_id'
})
YIELD componentCount, computeMillis;

CALL gds.graph.nodeProperties.write($graph_name, ['wcc_id'])
YIELD propertiesWritten
RETURN propertiesWritten;
