// =============================================================================
// FinGraph API Cypher: Account Queries
// =============================================================================

// List Accounts with owner, host bank, and GDS metrics
MATCH (a:Account)
OPTIONAL MATCH (p:Person)-[:OWNS]->(a)
OPTIONAL MATCH (a)-[:HOSTED_BY]->(b:Bank)
RETURN
    a.account_id AS account_id,
    a.account_type AS account_type,
    a.risk_score AS risk_score,
    a.risk_level AS risk_level,
    p.person_id AS owner_id,
    p.name AS owner_name,
    b.bank_id AS bank_id,
    b.name AS bank_name
ORDER BY a.risk_score DESC;
