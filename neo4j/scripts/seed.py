#!/usr/bin/env python3
"""
FinGraph Neo4j Deterministic Graph Seeder.
Populates a fresh or existing Neo4j database with deterministic banks, people, accounts,
and transactions covering normal activity and all 5 fraud syndicate topologies.
"""
import logging
import sys
from pathlib import Path

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from neo4j.src.client import Neo4jClient
from neo4j.src.config import get_neo4j_config
from neo4j.seed.seed_data import (
    SEED_BANKS,
    SEED_PEOPLE,
    SEED_ACCOUNTS,
    SEED_TRANSACTIONS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SeedGraph] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FinGraph.SeedGraph")


def seed_database(client: Neo4jClient) -> dict:
    """Executes idempotent MERGE operations to seed the graph database."""
    logger.info("Seeding Banks...")
    for bank in SEED_BANKS:
        client.execute_write(
            """
            MERGE (b:Bank {bank_id: $bank_id})
            ON CREATE SET b.name = $name, b.country = $country, b.routing_number = $routing_number
            ON MATCH SET b.name = $name, b.country = $country
            """,
            bank,
        )

    logger.info("Seeding People & Entities...")
    for person in SEED_PEOPLE:
        client.execute_write(
            """
            MERGE (p:Person {person_id: $person_id})
            ON CREATE SET p.name = $name, p.country = $country
            ON MATCH SET p.name = $name
            """,
            person,
        )

    logger.info("Seeding Accounts & Ownerships...")
    for acc in SEED_ACCOUNTS:
        client.execute_write(
            """
            MERGE (a:Account {account_id: $account_id})
            ON CREATE SET a.account_type = $account_type, a.risk_score = $risk_score, a.is_frozen = false
            ON MATCH SET a.account_type = $account_type, a.risk_score = $risk_score
            WITH a
            MATCH (p:Person {person_id: $owner_id})
            MERGE (p)-[:OWNS]->(a)
            WITH a
            MATCH (b:Bank {bank_id: $bank_id})
            MERGE (a)-[:HOSTED_BY]->(b)
            """,
            acc,
        )

    logger.info("Seeding Transactions & Transfer Edges...")
    scenario_counts = {}
    for tx in SEED_TRANSACTIONS:
        client.execute_write(
            """
            MATCH (src:Account {account_id: $from_account})
            MATCH (dst:Account {account_id: $to_account})
            MERGE (src)-[r:TRANSFERRED_TO {transaction_id: $transaction_id}]->(dst)
            ON CREATE SET
                r.amount = $amount,
                r.currency = $currency,
                r.timestamp = datetime($timestamp),
                r.scenario_id = $scenario_id,
                r.transaction_type = $transaction_type,
                r.channel = $channel
            ON MATCH SET
                r.amount = $amount,
                r.currency = $currency,
                r.scenario_id = $scenario_id
            """,
            tx,
        )
        sc = tx["scenario_id"]
        scenario_counts[sc] = scenario_counts.get(sc, 0) + 1

    # Verify counts in graph
    node_counts = client.execute_query(
        """
        RETURN
            count { MATCH (:Bank) } AS banks,
            count { MATCH (:Person) } AS people,
            count { MATCH (:Account) } AS accounts,
            count { MATCH ()-[r:TRANSFERRED_TO]->() } AS transfers
        """
    )
    counts = node_counts[0] if node_counts else {}

    return {
        "banks": counts.get("banks", len(SEED_BANKS)),
        "people": counts.get("people", len(SEED_PEOPLE)),
        "accounts": counts.get("accounts", len(SEED_ACCOUNTS)),
        "transactions": counts.get("transfers", len(SEED_TRANSACTIONS)),
        "scenarios": scenario_counts,
    }


def main():
    print("=" * 70)
    print("  FinGraph Neo4j Deterministic Graph Seeder")
    print("=" * 70)

    config = get_neo4j_config()
    try:
        with Neo4jClient(config=config, auto_connect=True) as client:
            if not client.verify_connectivity():
                print(f"[FATAL] Cannot connect to Neo4j at {config.uri}. Ensure Neo4j is running.")
                sys.exit(1)

            print(f"[*] Connected to Neo4j at {config.uri}")
            summary = seed_database(client)

            print("\n" + "=" * 70)
            print("  Seed Summary")
            print("=" * 70)
            print(f"  Banks in Graph:        {summary['banks']}")
            print(f"  People in Graph:       {summary['people']}")
            print(f"  Accounts in Graph:     {summary['accounts']}")
            print(f"  Transactions in Graph: {summary['transactions']}")
            print("  Scenario Breakdown:")
            for sc, count in sorted(summary["scenarios"].items()):
                print(f"    - {sc:<25} : {count:>3} transactions")
            print("  Status:                SEED COMPLETE & IDEMPOTENT")
            print("=" * 70)

    except Exception as exc:
        print(f"\n[ERROR] Graph seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
