// =============================================================================
// FinGraph API Cypher: Bounded Neighborhood Graph Subgraph Query
// =============================================================================

MATCH path = (root:Account {account_id: $account_id})-[r:TRANSFERRED_TO*1..2]-(neighbor:Account)
UNWIND relationships(path) AS rel
WITH startNode(rel) AS src, endNode(rel) AS dst, rel
RETURN DISTINCT
    src.account_id AS source,
    dst.account_id AS target,
    rel.transaction_id AS tx_id,
    rel.amount AS amount,
    coalesce(rel.currency, 'USD') AS currency,
    rel.timestamp AS timestamp
LIMIT 250;
