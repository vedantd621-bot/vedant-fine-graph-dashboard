// =============================================================================
// FinGraph Detection Query: Funnel / Smurfing Topology
// =============================================================================
// Identifies intermediary accounts receiving structured inflows from multiple
// source accounts and subsequent consolidation into a destination exit account.

MATCH (src:Account)-[r1:TRANSFERRED_TO]->(mule:Account)-[r2:TRANSFERRED_TO]->(dst:Account)
WHERE src <> dst AND src <> mule AND mule <> dst
  AND ($start_time IS NULL OR r1.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r1.timestamp <= datetime($end_time))
  AND ($start_time IS NULL OR r2.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r2.timestamp <= datetime($end_time))
WITH mule, dst,
     collect(DISTINCT src.account_id) AS source_accounts,
     count(DISTINCT src) AS source_count,
     sum(r1.amount) AS total_inflow,
     r2.amount AS sweep_outflow,
     collect(DISTINCT r1.transaction_id) + [r2.transaction_id] AS tx_ids,
     r1.scenario_id AS scenario_id
WHERE source_count >= $min_sources
  AND total_inflow >= $min_amount
RETURN
    mule.account_id AS mule_account,
    dst.account_id AS destination_account,
    source_accounts,
    source_count,
    total_inflow,
    sweep_outflow,
    tx_ids,
    scenario_id
ORDER BY source_count DESC, total_inflow DESC;
