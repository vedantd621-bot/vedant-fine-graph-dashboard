// =============================================================================
// FinGraph Detection Query: Multi-Tier Layered Syndicate Network
// =============================================================================
// Identifies 4-tier topologies: Sources -> Intermediaries -> Central Aggregator -> Destinations

MATCH (src:Account)-[r1:TRANSFERRED_TO]->(inter:Account)-[r2:TRANSFERRED_TO]->(agg:Account)-[r3:TRANSFERRED_TO]->(dst:Account)
WHERE src <> inter AND inter <> agg AND agg <> dst AND src <> dst AND src <> agg AND inter <> dst
  AND ($start_time IS NULL OR r1.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r1.timestamp <= datetime($end_time))
  AND ($start_time IS NULL OR r2.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r2.timestamp <= datetime($end_time))
  AND ($start_time IS NULL OR r3.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r3.timestamp <= datetime($end_time))
WITH agg,
     collect(DISTINCT src.account_id) AS sources,
     collect(DISTINCT inter.account_id) AS intermediaries,
     collect(DISTINCT dst.account_id) AS destinations,
     collect(DISTINCT r1.transaction_id) + collect(DISTINCT r2.transaction_id) + collect(DISTINCT r3.transaction_id) AS tx_ids,
     sum(r1.amount) AS total_inflow,
     r1.scenario_id AS scenario_id
WHERE size(sources) >= $min_sources
  AND size(intermediaries) >= $min_intermediaries
  AND size(destinations) >= $min_destinations
RETURN
    agg.account_id AS aggregator_account,
    sources,
    size(sources) AS source_count,
    intermediaries,
    size(intermediaries) AS intermediary_count,
    destinations,
    size(destinations) AS destination_count,
    total_inflow,
    tx_ids,
    scenario_id
ORDER BY total_inflow DESC;
