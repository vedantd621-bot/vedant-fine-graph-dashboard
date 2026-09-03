// =============================================================================
// FinGraph Detection Query: Circular Flow / Wash Trading Loop
// =============================================================================
// Identifies closed directed loops where funds return to origin accounts.

MATCH path = (a:Account)-[rels:TRANSFERRED_TO*2..5]->(a)
WHERE ($start_time IS NULL OR ALL(r IN rels WHERE r.timestamp >= datetime($start_time)))
  AND ($end_time IS NULL OR ALL(r IN rels WHERE r.timestamp <= datetime($end_time)))
WITH [node IN nodes(path) | node.account_id] AS cycle_nodes,
     [rel IN rels | rel.transaction_id] AS tx_ids,
     [rel IN rels | rel.amount] AS amounts,
     [rel IN rels | rel.scenario_id] AS scenarios,
     length(path) AS cycle_length
RETURN DISTINCT
    cycle_nodes,
    cycle_length,
    tx_ids,
    amounts,
    scenarios[0] AS scenario_id
ORDER BY cycle_length ASC;
