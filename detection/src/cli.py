#!/usr/bin/env python3
"""
FinGraph Fraud Detection CLI.
Provides command-line execution for topological fraud pattern detectors,
generating explainable human-readable reports or JSON outputs.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from detection.src.config import get_detection_config
from detection.src.engine import DetectionEngine
from detection.src.models import DetectionResult

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] [DetectionCLI] %(message)s",
    datefmt="%H:%M:%S",
)


def print_text_report(results: List[DetectionResult]):
    """Renders human-readable formatted report for compliance/fraud analysts."""
    print("=" * 80)
    print(f"  FinGraph Fraud Syndicate Detection Report ({len(results)} Findings)")
    print("=" * 80)

    if not results:
        print("\n  [✓] No suspicious graph patterns detected matching the criteria.\n")
        print("=" * 80)
        return

    for idx, res in enumerate(results, 1):
        print(f"\n[{idx}] Detection: {res.detection_type.value}")
        print("-" * 80)
        print(f"  Detection ID:     {res.detection_id}")
        print(f"  Severity:         {res.severity.value}")
        print(f"  Confidence:       {res.confidence * 100:.1f}%")
        print(f"  Primary Account:  {res.primary_account}")
        if res.scenario_id:
            print(f"  Scenario Tag:     {res.scenario_id}")
        if res.total_amount:
            print(f"  Total Volume:     ${res.total_amount:,.2f} {res.currency}")
        print(f"  Summary:          {res.description}")
        print(f"  Evidence:         {res.evidence.reason_summary}")
        if res.related_accounts:
            print(f"  Related Accounts: {', '.join(res.related_accounts)}")
        if res.transaction_ids:
            print(f"  Transaction IDs:  {', '.join(res.transaction_ids[:6])}" + ("..." if len(res.transaction_ids) > 6 else ""))

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="FinGraph Cypher Graph Fraud Detection Engine")
    parser.add_argument("--all", action="store_true", help="Run all enabled graph detectors")
    parser.add_argument("--funnel", action="store_true", help="Run Funnel/Smurfing detector")
    parser.add_argument("--one-to-many", action="store_true", help="Run One-to-Many distribution detector")
    parser.add_argument("--chain", action="store_true", help="Run Intermediary multi-hop chain detector")
    parser.add_argument("--circular", action="store_true", help="Run Circular flow / wash trading detector")
    parser.add_argument("--layered", action="store_true", help="Run Layered multi-tier syndicate detector")
    parser.add_argument("--high-degree", action="store_true", help="Run High-degree hub account detector")
    parser.add_argument("--money-trail", action="store_true", help="Trace forensic money trail")

    # Threshold overrides
    parser.add_argument("--min-sources", type=int, default=None)
    parser.add_argument("--min-destinations", type=int, default=None)
    parser.add_argument("--min-depth", type=int, default=None)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--min-degree", type=int, default=None)
    parser.add_argument("--from-account", type=str, default=None)
    parser.add_argument("--to-account", type=str, default=None)

    # Output formatting
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--dry-run", action="store_true", help="Validate CLI and engine without live DB")
    args = parser.parse_args()

    # Default to --all if no specific detector flag selected
    if not (args.funnel or args.one_to_many or args.chain or args.circular or args.layered or args.high_degree or args.money_trail or args.all):
        args.all = True

    config = get_detection_config()

    if args.dry_run:
        print("[*] Dry run mode: Initializing DetectionEngine in offline mode...")
        engine = DetectionEngine(config=config, auto_connect=False)
        engine.close()
        print("[SUCCESS] Detection Engine initialized successfully in offline mode.")
        return

    try:
        with DetectionEngine(config=config, auto_connect=True) as engine:
            if not engine.client.verify_connectivity():
                print(f"[FATAL] Cannot reach Neo4j at {config.neo4j_uri}. Ensure database is running.", file=sys.stderr)
                sys.exit(1)

            results: List[DetectionResult] = []

            if args.all:
                results = engine.run_all()
            else:
                if args.circular:
                    results.extend(engine.detect_circular_flows())
                if args.funnel:
                    kwargs = {}
                    if args.min_sources:
                        kwargs["min_sources"] = args.min_sources
                    results.extend(engine.detect_funnels(**kwargs))
                if args.one_to_many:
                    kwargs = {}
                    if args.min_destinations:
                        kwargs["min_destinations"] = args.min_destinations
                    results.extend(engine.detect_one_to_many(**kwargs))
                if args.chain:
                    kwargs = {}
                    if args.min_depth:
                        kwargs["min_depth"] = args.min_depth
                    if args.max_depth:
                        kwargs["max_depth"] = args.max_depth
                    results.extend(engine.detect_chains(**kwargs))
                if args.layered:
                    results.extend(engine.detect_layered_networks())
                if args.high_degree:
                    kwargs = {}
                    if args.min_degree:
                        kwargs["min_degree"] = args.min_degree
                    results.extend(engine.detect_high_degree_accounts(**kwargs))
                if args.money_trail:
                    from_acc = args.from_account or "A001"
                    results.extend(engine.trace_money_trail(from_account=from_acc, to_account=args.to_account))

            if args.format == "json":
                out_data = [r.model_dump(mode="json") for r in results]
                print(json.dumps(out_data, indent=2))
            else:
                print_text_report(results)

    except Exception as exc:
        print(f"[ERROR] Detection execution failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
