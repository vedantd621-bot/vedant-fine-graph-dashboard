// =============================================================================
// FinGraph API Cypher: Dashboard Aggregates Query
// =============================================================================

MATCH (a:Account)
OPTIONAL MATCH ()-[r:TRANSFERRED_TO]->()
RETURN
    count(DISTINCT a) AS total_accounts,
    count(DISTINCT r) AS total_transactions,
    coalesce(sum(r.amount), 0.0) AS total_volume;
