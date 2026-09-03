"""
FinGraph Parameterized Cypher Fraud Detection & Query Library.
Provides clean Python wrapper functions for querying account networks,
tracing money trails, and detecting topological fraud patterns (Funnels, Cycles, Distributions, Chains).
"""
from typing import Any, Dict, List, Optional
from neo4j.src.client import Neo4jClient


def get_account_details(client: Neo4jClient, account_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full profile for an account, including owner person and host bank."""
    query = """
    MATCH (a:Account {account_id: $account_id})
    OPTIONAL MATCH (p:Person)-[:OWNS]->(a)
    OPTIONAL MATCH (a)-[:HOSTED_BY]->(b:Bank)
    RETURN
        a.account_id AS account_id,
        a.account_type AS account_type,
        a.risk_score AS risk_score,
        a.is_frozen AS is_frozen,
        a.community_id AS community_id,
        a.pagerank AS pagerank,
        p.person_id AS owner_person_id,
        p.name AS owner_name,
        p.country AS owner_country,
        b.bank_id AS bank_id,
        b.name AS bank_name,
        b.country AS bank_country
    """
    records = client.execute_query(query, {"account_id": account_id})
    return records[0] if records else None


def get_account_counterparties(client: Neo4jClient, account_id: str) -> List[Dict[str, Any]]:
    """Retrieves direct 1-hop incoming and outgoing counterparties for an account."""
    query = """
    MATCH (a:Account {account_id: $account_id})
    OPTIONAL MATCH (a)<-[in_r:TRANSFERRED_TO]-(in_acc:Account)
    OPTIONAL MATCH (a)-[out_r:TRANSFERRED_TO]->(out_acc:Account)
    WITH
        collect(DISTINCT {
            counterparty: in_acc.account_id,
            direction: 'INCOMING',
            transaction_id: in_r.transaction_id,
            amount: in_r.amount,
            currency: in_r.currency,
            timestamp: toString(in_r.timestamp),
            scenario_id: in_r.scenario_id
        }) AS incoming,
        collect(DISTINCT {
            counterparty: out_acc.account_id,
            direction: 'OUTGOING',
            transaction_id: out_r.transaction_id,
            amount: out_r.amount,
            currency: out_r.currency,
            timestamp: toString(out_r.timestamp),
            scenario_id: out_r.scenario_id
        }) AS outgoing
    RETURN [item IN (incoming + outgoing) WHERE item.counterparty IS NOT NULL] AS counterparties
    """
    records = client.execute_query(query, {"account_id": account_id})
    return records[0]["counterparties"] if records else []


def get_high_degree_accounts(client: Neo4jClient, min_degree: int = 3, limit: int = 20) -> List[Dict[str, Any]]:
    """Identifies highly connected hub accounts (fan-in + fan-out)."""
    query = """
    MATCH (a:Account)
    OPTIONAL MATCH (a)<-[in_r:TRANSFERRED_TO]-()
    OPTIONAL MATCH (a)-[out_r:TRANSFERRED_TO]->()
    WITH a, count(DISTINCT in_r) AS in_degree, count(DISTINCT out_r) AS out_degree
    WITH a, in_degree, out_degree, (in_degree + out_degree) AS total_degree
    WHERE total_degree >= $min_degree
    RETURN
        a.account_id AS account_id,
        a.account_type AS account_type,
        a.risk_score AS risk_score,
        in_degree,
        out_degree,
        total_degree
    ORDER BY total_degree DESC, a.risk_score DESC
    LIMIT $limit
    """
    return client.execute_query(query, {"min_degree": min_degree, "limit": limit})


def detect_circular_flows(client: Neo4jClient, min_hops: int = 2, max_hops: int = 5) -> List[Dict[str, Any]]:
    """
    Detects closed-loop wash trading cycles: A -> B -> ... -> A.
    Uses parameterized depth range.
    """
    # Cypher allows variable length in range
    query = f"""
    MATCH path = (a:Account)-[:TRANSFERRED_TO*{min_hops}..{max_hops}]->(a)
    WITH [node IN nodes(path) | node.account_id] AS cycle_nodes,
         [rel IN relationships(path) | rel.transaction_id] AS tx_ids,
         [rel IN relationships(path) | rel.amount] AS amounts,
         [rel IN relationships(path) | rel.scenario_id] AS scenarios,
         length(path) AS cycle_length
    RETURN DISTINCT
        cycle_nodes,
        cycle_length,
        tx_ids,
        amounts,
        scenarios[0] AS scenario_id
    ORDER BY cycle_length ASC
    """
    return client.execute_query(query)


def detect_funnel_patterns(client: Neo4jClient, min_sources: int = 3) -> List[Dict[str, Any]]:
    """
    Detects funnel/smurfing topologies where multiple source accounts
    transfer to an intermediary mule, which sweeps out to a beneficiary account.
    """
    query = """
    MATCH (src:Account)-[r1:TRANSFERRED_TO]->(mule:Account)-[r2:TRANSFERRED_TO]->(dst:Account)
    WHERE src <> dst AND src <> mule AND mule <> dst
    WITH mule, dst,
         collect(DISTINCT src.account_id) AS source_accounts,
         count(DISTINCT src) AS source_count,
         sum(r1.amount) AS total_inflow,
         r2.amount AS outflow_amount,
         r2.transaction_id AS sweep_tx_id,
         r1.scenario_id AS scenario_id
    WHERE source_count >= $min_sources
    RETURN
        mule.account_id AS mule_account,
        dst.account_id AS destination_account,
        source_accounts,
        source_count,
        total_inflow,
        outflow_amount,
        sweep_tx_id,
        scenario_id
    ORDER BY source_count DESC
    """
    return client.execute_query(query, {"min_sources": min_sources})


def detect_distribution_patterns(client: Neo4jClient, min_destinations: int = 4) -> List[Dict[str, Any]]:
    """
    Detects 1-to-many dispersion hubs where a single source transfers to many accounts.
    """
    query = """
    MATCH (src:Account)-[r:TRANSFERRED_TO]->(dst:Account)
    WITH src,
         collect(DISTINCT dst.account_id) AS destination_accounts,
         count(DISTINCT dst) AS destination_count,
         sum(r.amount) AS total_disbursed,
         r.scenario_id AS scenario_id
    WHERE destination_count >= $min_destinations
    RETURN
        src.account_id AS source_account,
        destination_accounts,
        destination_count,
        total_disbursed,
        scenario_id
    ORDER BY destination_count DESC
    """
    return client.execute_query(query, {"min_destinations": min_destinations})


def detect_intermediary_chains(client: Neo4jClient, min_hops: int = 3, max_hops: int = 6) -> List[Dict[str, Any]]:
    """
    Detects linear pass-through chains: A -> B -> C -> D.
    """
    query = f"""
    MATCH path = (origin:Account)-[:TRANSFERRED_TO*{min_hops}..{max_hops}]->(exit:Account)
    WHERE origin <> exit AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE x = y))
    WITH [node IN nodes(path) | node.account_id] AS chain_nodes,
         [rel IN relationships(path) | rel.amount] AS amounts,
         [rel IN relationships(path) | rel.scenario_id] AS scenarios,
         length(path) AS hop_count
    RETURN DISTINCT
        chain_nodes,
        hop_count,
        amounts,
        scenarios[0] AS scenario_id
    ORDER BY hop_count DESC
    LIMIT 20
    """
    return client.execute_query(query)


def trace_money_trail(client: Neo4jClient, account_id: str, depth: int = 3) -> List[Dict[str, Any]]:
    """
    Traces multi-hop paths entering or leaving a focal account for forensic trail visualization.
    """
    query = f"""
    MATCH path = (a:Account {{account_id: $account_id}})-[:TRANSFERRED_TO*1..{depth}]-(connected:Account)
    RETURN
        [node IN nodes(path) | {{
            account_id: node.account_id,
            account_type: node.account_type,
            risk_score: node.risk_score
        }}] AS path_nodes,
        [rel IN relationships(path) | {{
            transaction_id: rel.transaction_id,
            amount: rel.amount,
            currency: rel.currency,
            timestamp: toString(rel.timestamp),
            scenario_id: rel.scenario_id
        }}] AS path_edges,
        length(path) AS path_length
    LIMIT 50
    """
    return client.execute_query(query, {"account_id": account_id})


def get_scenario_transactions(client: Neo4jClient, scenario_id: str) -> List[Dict[str, Any]]:
    """Retrieves all transaction records matching a specific test scenario tag."""
    query = """
    MATCH (src:Account)-[r:TRANSFERRED_TO {scenario_id: $scenario_id}]->(dst:Account)
    RETURN
        r.transaction_id AS transaction_id,
        src.account_id AS from_account,
        dst.account_id AS to_account,
        r.amount AS amount,
        r.currency AS currency,
        toString(r.timestamp) AS timestamp,
        r.scenario_id AS scenario_id,
        r.transaction_type AS transaction_type,
        r.channel AS channel
    ORDER BY r.timestamp ASC
    """
    return client.execute_query(query, {"scenario_id": scenario_id})
