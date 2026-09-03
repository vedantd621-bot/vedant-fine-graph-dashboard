// =============================================================================
// FinGraph GDS Cypher: In-Memory Analytical Graph Projection
// =============================================================================

// 1. Drop existing projection if present
CALL gds.graph.drop($graph_name, false) YIELD graphName;

// 2. Project Account nodes and weighted TRANSFERRED_TO edges
CALL gds.graph.project(
    $graph_name,
    'Account',
    {
        TRANSFERRED_TO: {
            type: 'TRANSFERRED_TO',
            orientation: 'NATURAL',
            properties: ['amount']
        }
    }
)
YIELD graphName, nodeCount, relationshipCount, projectMillis
RETURN graphName, nodeCount, relationshipCount, projectMillis;
