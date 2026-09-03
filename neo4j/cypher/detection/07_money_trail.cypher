// =============================================================================
// FinGraph Detection Query: Multi-Hop Forensic Money Trail
// =============================================================================
// Traces directed money flow paths between specific accounts or outwards from a source.

MATCH path = (src:Account {account_id: $from_account})-[rels:TRANSFERRED_TO*1..4]->(dst:Account)
WHERE ($to_account IS NULL OR dst.account_id = $to_account)
  AND ($start_time IS NULL OR ALL(r IN rels WHERE r.timestamp >= datetime($start_time)))
  AND ($end_time IS NULL OR ALL(r IN rels WHERE r.timestamp <= datetime($end_time)))
WITH [node IN nodes(path) | node.account_id] AS path_nodes,
     [rel IN rels | rel.transaction_id] AS tx_ids,
     [rel IN rels | rel.amount] AS amounts,
     [rel IN rels | rel.scenario_id] AS scenarios,
     length(path) AS path_len
RETURN DISTINCT
    path_nodes,
    path_len,
    tx_ids,
    amounts,
    scenarios[0] AS scenario_id
LIMIT $limit;
