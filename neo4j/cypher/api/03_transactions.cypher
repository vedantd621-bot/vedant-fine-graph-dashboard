// =============================================================================
// FinGraph API Cypher: Account Transactions Query
// =============================================================================

MATCH (a:Account {account_id: $account_id})
OPTIONAL MATCH (src:Account)-[in_r:TRANSFERRED_TO]->(a)
OPTIONAL MATCH (a)-[out_r:TRANSFERRED_TO]->(dst:Account)
WITH
    collect(DISTINCT {
        tx_id: in_r.transaction_id,
        dir: 'INCOMING',
        counterparty: src.account_id,
        amount: in_r.amount,
        currency: coalesce(in_r.currency, 'USD'),
        timestamp: in_r.timestamp,
        scenario_id: in_r.scenario_id
    }) +
    collect(DISTINCT {
        tx_id: out_r.transaction_id,
        dir: 'OUTGOING',
        counterparty: dst.account_id,
        amount: out_r.amount,
        currency: coalesce(out_r.currency, 'USD'),
        timestamp: out_r.timestamp,
        scenario_id: out_r.scenario_id
    }) AS raw_txs
UNWIND raw_txs AS tx
WITH tx WHERE tx.tx_id IS NOT NULL
RETURN
    tx.tx_id AS transaction_id,
    tx.dir AS direction,
    tx.counterparty AS counterparty,
    tx.amount AS amount,
    tx.currency AS currency,
    tx.timestamp AS timestamp,
    tx.scenario_id AS scenario_id
ORDER BY timestamp DESC;
