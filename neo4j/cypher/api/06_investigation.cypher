// =============================================================================
// FinGraph API Cypher: Multi-Hop Forensic Money Trail Query
// =============================================================================

MATCH path = (src:Account {account_id: $from_account})-[rels:TRANSFERRED_TO*1..4]->(dst:Account)
WHERE ($to_account IS NULL OR dst.account_id = $to_account)
WITH [node IN nodes(path) | node.account_id] AS path_nodes,
     [rel IN rels | rel.transaction_id] AS tx_ids,
     [rel IN rels | rel.amount] AS amounts,
     [rel IN rels | rel.scenario_id] AS scenarios,
     length(path) AS hop_count
RETURN DISTINCT
    path_nodes,
    hop_count,
    tx_ids,
    amounts,
    scenarios[0] AS scenario_id
LIMIT 25;
