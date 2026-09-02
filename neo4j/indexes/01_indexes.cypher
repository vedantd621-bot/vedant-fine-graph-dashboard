// =============================================================================
// FinGraph: Neo4j Performance Indexes
// Enable sub-100ms multi-hop path and risk analytics queries
// =============================================================================

// Index on Account Risk Score for fast threshold filtering
CREATE INDEX idx_account_risk_score IF NOT EXISTS
FOR (a:Account)
ON (a.risk_score);

// Index on Account Community ID for fast syndicate clustering
CREATE INDEX idx_account_community_id IF NOT EXISTS
FOR (a:Account)
ON (a.community_id);

// Index on Person Name for analyst search
CREATE INDEX idx_person_name IF NOT EXISTS
FOR (p:Person)
ON (p.name);

// Index on TRANSFERRED_TO timestamp for temporal window queries
CREATE INDEX idx_rel_transferred_timestamp IF NOT EXISTS
FOR ()-[r:TRANSFERRED_TO]-()
ON (r.timestamp);

// Index on TRANSFERRED_TO scenario_id for test scenario validation
CREATE INDEX idx_rel_transferred_scenario IF NOT EXISTS
FOR ()-[r:TRANSFERRED_TO]-()
ON (r.scenario_id);
