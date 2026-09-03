// =============================================================================
// FinGraph Detection Query: High-Degree Hub Accounts
// =============================================================================
// Identifies accounts with unusually high graph degree (in-degree + out-degree).

MATCH (a:Account)
OPTIONAL MATCH (a)<-[in_r:TRANSFERRED_TO]-()
  WHERE ($start_time IS NULL OR in_r.timestamp >= datetime($start_time))
    AND ($end_time IS NULL OR in_r.timestamp <= datetime($end_time))
OPTIONAL MATCH (a)-[out_r:TRANSFERRED_TO]->()
  WHERE ($start_time IS NULL OR out_r.timestamp >= datetime($start_time))
    AND ($end_time IS NULL OR out_r.timestamp <= datetime($end_time))
WITH a, count(DISTINCT in_r) AS in_degree, count(DISTINCT out_r) AS out_degree
WITH a, in_degree, out_degree, (in_degree + out_degree) AS total_degree
WHERE total_degree >= $min_degree
RETURN
    a.account_id AS account_id,
    a.account_type AS account_type,
    a.risk_score AS risk_score,
    in_degree,
    out_degree,
    total_degree
ORDER BY total_degree DESC, a.risk_score DESC
LIMIT $limit;
