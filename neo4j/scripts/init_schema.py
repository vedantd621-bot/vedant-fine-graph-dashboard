#!/usr/bin/env python3
"""
FinGraph Neo4j Schema & Constraints Initializer.
Applies all uniqueness constraints and performance indexes idempotently.
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [InitSchema] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FinGraph.InitSchema")


def apply_schema(client: Neo4jClient) -> dict:
    """Reads and executes all constraint and index cypher definitions."""
    constraints_path = root_dir / "neo4j" / "constraints" / "schema.cypher"
    indexes_path = root_dir / "neo4j" / "indexes" / "indexes.cypher"

    if not constraints_path.is_file():
        raise FileNotFoundError(f"Missing constraints file: {constraints_path}")
    if not indexes_path.is_file():
        raise FileNotFoundError(f"Missing indexes file: {indexes_path}")

    constraints_cypher = constraints_path.read_text(encoding="utf-8")
    indexes_cypher = indexes_path.read_text(encoding="utf-8")

    logger.info("Applying uniqueness constraints...")
    c_results = client.execute_script(constraints_cypher)
    logger.info(f"Executed {len(c_results)} constraint statements.")

    logger.info("Applying performance indexes...")
    i_results = client.execute_script(indexes_cypher)
    logger.info(f"Executed {len(i_results)} index statements.")

    # Query active constraints and indexes from dbms
    try:
        active_constraints = client.execute_query("SHOW CONSTRAINTS")
        active_indexes = client.execute_query("SHOW INDEXES")
    except Exception:
        active_constraints = []
        active_indexes = []

    return {
        "constraints_applied": len(c_results),
        "indexes_applied": len(i_results),
        "total_active_constraints": len(active_constraints),
        "total_active_indexes": len(active_indexes),
    }


def main():
    print("=" * 70)
    print("  FinGraph Neo4j Schema Initializer")
    print("=" * 70)

    config = get_neo4j_config()
    try:
        with Neo4jClient(config=config, auto_connect=True) as client:
            if not client.verify_connectivity():
                print(f"[FATAL] Cannot connect to Neo4j at {config.uri}. Ensure Neo4j is running.")
                sys.exit(1)

            print(f"[*] Connected to Neo4j at {config.uri} (Database: {config.database})")
            summary = apply_schema(client)

            print("\n" + "=" * 70)
            print("  Schema Initialization Summary")
            print("=" * 70)
            print(f"  Constraints Executed:    {summary['constraints_applied']}")
            print(f"  Indexes Executed:        {summary['indexes_applied']}")
            print(f"  Active DBMS Constraints: {summary['total_active_constraints']}")
            print(f"  Active DBMS Indexes:     {summary['total_active_indexes']}")
            print("  Status:                  IDEMPOTENT & READY")
            print("=" * 70)

    except Exception as exc:
        print(f"\n[ERROR] Schema initialization failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
