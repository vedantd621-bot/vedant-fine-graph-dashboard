// =============================================================================
// FinGraph Detection Query: Intermediary Multi-Hop Pass-Through Chain
// =============================================================================
// Identifies linear layering sequences traversing multiple intermediate accounts.

MATCH path = (origin:Account)-[rels:TRANSFERRED_TO*3..6]->(exit:Account)
WHERE origin <> exit
  AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE x = y))
  AND ($start_time IS NULL OR ALL(r IN rels WHERE r.timestamp >= datetime($start_time)))
  AND ($end_time IS NULL OR ALL(r IN rels WHERE r.timestamp <= datetime($end_time)))
WITH [node IN nodes(path) | node.account_id] AS chain_nodes,
     [rel IN rels | rel.transaction_id] AS tx_ids,
     [rel IN rels | rel.amount] AS amounts,
     [rel IN rels | rel.scenario_id] AS scenarios,
     length(path) AS hop_count
WHERE hop_count >= $min_depth AND hop_count <= $max_depth
RETURN DISTINCT
    chain_nodes,
    hop_count,
    tx_ids,
    amounts,
    scenarios[0] AS scenario_id
ORDER BY hop_count DESC
LIMIT 50;
