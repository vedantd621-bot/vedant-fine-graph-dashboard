// =============================================================================
// FinGraph API Cypher: Alert Queries
// =============================================================================

// 1. List Alerts with Account & Risk context
MATCH (a:Account)
OPTIONAL MATCH ()-[r:TRANSFERRED_TO]->(a)
RETURN
    a.account_id AS primary_account,
    a.risk_score AS risk_score,
    a.risk_level AS risk_level
ORDER BY a.risk_score DESC;
