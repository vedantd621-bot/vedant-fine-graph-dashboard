// =============================================================================
// FinGraph Detection Query: One-to-Many Distribution / Dispersion
// =============================================================================
// Identifies high-value source accounts disbursing funds to multiple destinations.

MATCH (src:Account)-[r:TRANSFERRED_TO]->(dst:Account)
WHERE src <> dst
  AND ($start_time IS NULL OR r.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r.timestamp <= datetime($end_time))
WITH src,
     collect(DISTINCT dst.account_id) AS destination_accounts,
     count(DISTINCT dst) AS destination_count,
     sum(r.amount) AS total_disbursed,
     collect(DISTINCT r.transaction_id) AS tx_ids,
     r.scenario_id AS scenario_id
WHERE destination_count >= $min_destinations
  AND total_disbursed >= $min_amount
RETURN
    src.account_id AS source_account,
    destination_accounts,
    destination_count,
    total_disbursed,
    tx_ids,
    scenario_id
ORDER BY destination_count DESC, total_disbursed DESC;
