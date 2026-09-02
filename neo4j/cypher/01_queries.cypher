// =============================================================================
// FinGraph: Fraud Detection Cypher Query Library
// Parameterized, optimized queries for topological anomaly detection
// =============================================================================

// -----------------------------------------------------------------------------
// 1. Direct Transfer Lookup
// -----------------------------------------------------------------------------
// Parameters: {from_account_id: 'A101', to_account_id: 'A205'}
MATCH (a:Account {account_id: $from_account_id})-[r:TRANSFERRED_TO]->(b:Account {account_id: $to_account_id})
RETURN a, r, b;

// -----------------------------------------------------------------------------
// 2. Circular Flow Detection (Cycles of length 3 to 5)
// Detects: A -> B -> C -> A
// -----------------------------------------------------------------------------
// Parameters: {account_id: 'A101', max_depth: 4}
MATCH path = (a:Account {account_id: $account_id})-[:TRANSFERRED_TO*2..5]->(a)
RETURN [node IN nodes(path) | node.account_id] AS cycle_path,
       length(path) AS cycle_length,
       [rel IN relationships(path) | rel.amount] AS transfer_amounts;

// -----------------------------------------------------------------------------
// 3. Funnel / Smurfing Pattern Detection
// Detects multiple source accounts sending to intermediary I, then I to B
// -----------------------------------------------------------------------------
// Parameters: {min_sources: 3, max_time_window_hours: 24}
MATCH (src:Account)-[r1:TRANSFERRED_TO]->(mule:Account)-[r2:TRANSFERRED_TO]->(dst:Account)
WHERE src <> dst AND src <> mule AND mule <> dst
WITH mule, dst, count(DISTINCT src) AS source_count, sum(r1.amount) AS total_in, sum(r2.amount) AS total_out
WHERE source_count >= $min_sources
RETURN mule.account_id AS mule_account,
       dst.account_id AS destination_account,
       source_count,
       total_in,
       total_out;

// -----------------------------------------------------------------------------
// 4. Money Trail / Multi-Hop Ingress & Egress Tracing
// -----------------------------------------------------------------------------
// Parameters: {account_id: 'A101', depth: 3}
MATCH path = (origin:Account {account_id: $account_id})-[:TRANSFERRED_TO*1..3]-(connected:Account)
RETURN path
LIMIT 50;

// -----------------------------------------------------------------------------
// 5. High-Degree Fan-In / Fan-Out Hub Detection
// -----------------------------------------------------------------------------
MATCH (a:Account)
OPTIONAL MATCH (a)<-[in_r:TRANSFERRED_TO]-()
OPTIONAL MATCH (a)-[out_r:TRANSFERRED_TO]->()
WITH a, count(DISTINCT in_r) AS in_degree, count(DISTINCT out_r) AS out_degree
WHERE in_degree > 10 OR out_degree > 10
RETURN a.account_id AS account_id,
       a.risk_score AS risk_score,
       in_degree,
       out_degree,
       (in_degree + out_degree) AS total_degree
ORDER BY total_degree DESC
LIMIT 20;
