// =============================================================================
// FinGraph GDS Cypher: Batch Risk Score & Feature Persistence
// =============================================================================

UNWIND $batch AS item
MATCH (a:Account {account_id: item.account_id})
SET a.risk_score = item.risk_score,
    a.risk_level = item.risk_level,
    a.risk_calculated_at = datetime(),
    a.risk_model_version = item.model_version,
    a.pagerank_score = item.pagerank_score,
    a.louvain_community_id = item.louvain_community_id,
    a.wcc_id = item.wcc_id,
    a.risk_reasons = item.reasons
RETURN count(a) AS updated_count;
