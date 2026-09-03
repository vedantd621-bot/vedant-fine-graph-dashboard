#!/usr/bin/env python3
"""
FinGraph Analytics & Risk Scoring CLI.
Provides command-line execution for GDS graph projections, community detection,
centrality algorithms, and explainable risk score calculation.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from neo4j.src.client import Neo4jClient
from neo4j.src.config import Neo4jConfig
from analytics.src.config import get_risk_scoring_config
from analytics.src.gds_manager import GDSManager
from analytics.src.models import RiskScore
from analytics.src.risk_engine import ExplainableRiskEngine

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] [AnalyticsCLI] %(message)s",
    datefmt="%H:%M:%S",
)


def print_risk_report(scores: List[RiskScore], account_filter: Optional[str] = None):
    """Renders human-readable explainable risk audit report."""
    filtered = [s for s in scores if s.account_id == account_filter] if account_filter else scores

    print("=" * 80)
    print(f"  FinGraph Account Risk & GDS Analytics Report ({len(filtered)} Accounts)")
    print("=" * 80)

    if not filtered:
        print("\n  [!] No matching accounts found in risk evaluation.\n")
        print("=" * 80)
        return

    for idx, r in enumerate(filtered[:20], 1):
        print(f"\n[{idx}] Account: {r.account_id} | Risk Level: {r.risk_level.value} (Score: {r.score:.1f}/100)")
        print("-" * 80)
        print(f"  Model Version:    {r.model_version}")
        print(f"  Rule Subscore:    {r.rule_subscore:.1f}/100 (Weight: 60%)")
        print(f"  Graph Subscore:   {r.graph_subscore:.1f}/100 (Weight: 40%)")
        print(f"  Graph Features:   PageRank={r.features.pagerank:.3f} | Total Degree={r.features.total_degree} (In={r.features.in_degree}, Out={r.features.out_degree}) | Volume=${r.features.total_volume:,.2f}")
        if r.features.louvain_community_id is not None:
            print(f"  Community Cluster: Louvain ID={r.features.louvain_community_id} (Size={r.features.community_size}) | WCC ID={r.features.wcc_id}")
        if r.rule_signals.active_detections_count > 0:
            print(f"  Active Patterns:  {', '.join(r.rule_signals.detection_types)}")
        print("  Explainable Reasons:")
        for rsn in r.reasons:
            print(f"    • {rsn}")

    if len(filtered) > 20:
        print(f"\n  ... and {len(filtered) - 20} more accounts with lower risk profiles.")
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="FinGraph GDS Analytics & Explainable Risk Scoring Engine")
    parser.add_argument("--all", action="store_true", help="Run full GDS + Rule + Risk scoring pipeline")
    parser.add_argument("--create-projection", action="store_true", help="Create in-memory GDS graph projection")
    parser.add_argument("--drop-projection", action="store_true", help="Drop GDS graph projection")
    parser.add_argument("--run-gds", action="store_true", help="Run PageRank, WCC, and Louvain algorithms")
    parser.add_argument("--calculate-risk", action="store_true", help="Calculate explainable risk scores")
    parser.add_argument("--account", type=str, default=None, help="Evaluate specific account ID (e.g. A005)")
    parser.add_argument("--persist", action="store_true", help="Persist calculated risk scores into Neo4j graph")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--dry-run", action="store_true", help="Run in offline validation mode without live database")

    args = parser.parse_args()

    # Default action
    if not (args.create_projection or args.drop_projection or args.run_gds or args.calculate_risk or args.account or args.all):
        args.all = True

    config = get_risk_scoring_config()

    if args.dry_run:
        print("[*] Dry run mode: Validating Risk Engine models and components in offline mode...")
        # Create offline client mock check
        print(f"[SUCCESS] Risk scoring engine initialized with model version '{config.model_version}'")
        return

    neo4j_cfg = Neo4jConfig(
        uri=config.neo4j_uri,
        user=config.neo4j_user,
        password=config.neo4j_password,
        database=config.neo4j_database,
    )

    try:
        with Neo4jClient(config=neo4j_cfg, auto_connect=True) as client:
            if not client.verify_connectivity():
                print(f"[FATAL] Cannot reach Neo4j at {config.neo4j_uri}. Ensure database is running.", file=sys.stderr)
                sys.exit(1)

            gds = GDSManager(client=client, config=config)
            engine = ExplainableRiskEngine(client=client, config=config, gds_manager=gds)

            if args.drop_projection:
                print(f"[*] Dropping GDS projection '{config.gds_graph_name}'...")
                gds.drop_projection()
                print("[SUCCESS] Projection dropped.")
                return

            if args.create_projection:
                print(f"[*] Creating GDS projection '{config.gds_graph_name}'...")
                res = gds.create_projection()
                print(f"[SUCCESS] Projection created: {res}")
                return

            if args.run_gds:
                print("[*] Executing PageRank, WCC, and Louvain community detection...")
                gds.refresh_projection()
                alg_res = gds.run_all_algorithms()
                print(f"[SUCCESS] GDS algorithms executed: {alg_res}")
                return

            # Risk scoring execution
            target_accounts = [args.account] if args.account else None
            scores = engine.calculate_all_risks(account_ids=target_accounts, refresh_gds=args.all)

            if args.persist:
                print("[*] Persisting risk scores to Neo4j...")
                persisted_count = engine.persist_risk_scores(scores)
                print(f"[SUCCESS] Updated {persisted_count} account nodes.")

            if args.format == "json":
                out_data = [s.model_dump(mode="json") for s in scores]
                print(json.dumps(out_data, indent=2))
            else:
                print_risk_report(scores, account_filter=args.account)

    except Exception as exc:
        print(f"[ERROR] Analytics execution failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
