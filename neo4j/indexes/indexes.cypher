// =============================================================================
// FinGraph: Neo4j Performance Indexes (Idempotent)
// Optimized for sub-100ms multi-hop path and risk analytics queries
// =============================================================================

// Index on Account Risk Score (for high-risk entity filtering)
CREATE INDEX idx_account_risk_score IF NOT EXISTS
FOR (a:Account)
ON (a.risk_score);

// Index on Account Community ID (for syndicate clustering queries)
CREATE INDEX idx_account_community_id IF NOT EXISTS
FOR (a:Account)
ON (a.community_id);

// Index on Account Type (for filtering retail vs business vs intermediary)
CREATE INDEX idx_account_type IF NOT EXISTS
FOR (a:Account)
ON (a.account_type);

// Index on Person Name (for analyst search lookups)
CREATE INDEX idx_person_name IF NOT EXISTS
FOR (p:Person)
ON (p.name);

// Index on Bank Name
CREATE INDEX idx_bank_name IF NOT EXISTS
FOR (b:Bank)
ON (b.name);

// Relationship Index on TRANSFERRED_TO transaction_id (for lookup by tx id)
CREATE INDEX idx_rel_transferred_tx_id IF NOT EXISTS
FOR ()-[r:TRANSFERRED_TO]-()
ON (r.transaction_id);

// Relationship Index on TRANSFERRED_TO timestamp (for temporal windowing)
CREATE INDEX idx_rel_transferred_timestamp IF NOT EXISTS
FOR ()-[r:TRANSFERRED_TO]-()
ON (r.timestamp);

// Relationship Index on TRANSFERRED_TO scenario_id (for scenario tracing)
CREATE INDEX idx_rel_transferred_scenario IF NOT EXISTS
FOR ()-[r:TRANSFERRED_TO]-()
ON (r.scenario_id);
