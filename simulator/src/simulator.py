#!/usr/bin/env python3
"""
FinGraph Simulator CLI.
Executes continuous synthetic transaction stream generation with configurable
throughput, account populations, scenario injection, and decoupled output sinks (stdout, file, Kafka).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Ensure project root in python path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from simulator.src.config import get_kafka_config
    from simulator.src.generator import FinGraphGenerator
    from simulator.src.models import ScenarioID
    from simulator.src.sinks import create_output_sink
except ImportError:
    from config import get_kafka_config
    from generator import FinGraphGenerator
    from models import ScenarioID
    from sinks import create_output_sink


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FinGraph Real-Time Synthetic Transaction Simulator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--rate", type=float, default=10.0, help="Target transactions per second (TPS)"
    )
    parser.add_argument(
        "--accounts", type=int, default=200, help="Number of synthetic accounts"
    )
    parser.add_argument(
        "--people", type=int, default=150, help="Number of synthetic people/entities"
    )
    parser.add_argument(
        "--banks", type=int, default=10, help="Number of synthetic banks"
    )
    parser.add_argument(
        "--suspicious-rate",
        type=float,
        default=0.20,
        help="Proportion of transactions generated from suspicious fraud patterns (0.0 - 1.0)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="stream",
        choices=[
            "stream",
            "SC_NORMAL",
            "SC_FUNNEL_01",
            "SC_DISTRIB_01",
            "SC_CHAIN_01",
            "SC_CIRCULAR_01",
            "SC_LAYERED_01",
            "all_scenarios",
        ],
        help="Generate continuous stream or specific isolated scenario",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration to run simulator in seconds (0 = infinite)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="stdout",
        help="Output destination: stdout | file:<filepath> | kafka",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Deterministic random seed"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress per-transaction log output"
    )
    return parser.parse_args()


def run_simulator():
    args = parse_args()

    print("=" * 70)
    print("  FinGraph Synthetic Transaction Simulator")
    print("=" * 70)
    print(f"  Target Rate:       {args.rate} TPS")
    print(f"  Account Pool:      {args.accounts} accounts ({args.people} people across {args.banks} banks)")
    print(f"  Suspicious Ratio:  {args.suspicious_rate * 100:.1f}%")
    print(f"  Mode / Scenario:   {args.scenario}")
    print(f"  Duration:          {'Infinite' if args.duration == 0 else f'{args.duration}s'}")
    print(f"  Random Seed:       {args.seed}")
    print(f"  Output Sink:       {args.output}")
    print("=" * 70)

    gen = FinGraphGenerator(
        num_accounts=args.accounts,
        num_people=args.people,
        num_banks=args.banks,
        seed=args.seed,
    )

    try:
        sink = create_output_sink(args.output, quiet=args.quiet)
    except Exception as exc:
        print(f"\n[FATAL] Failed to initialize output sink '{args.output}': {exc}", file=sys.stderr)
        sys.exit(1)

    total_emitted = 0
    scenario_counts = {}
    start_time = time.time()
    interval = 1.0 / max(0.1, args.rate)

    try:
        if args.scenario != "stream":
            # Specific scenario generation
            events = []
            if args.scenario == "SC_NORMAL":
                events = [gen.generate_normal_event() for _ in range(5)]
            elif args.scenario == "SC_FUNNEL_01":
                events = gen.generate_funnel_scenario()
            elif args.scenario == "SC_DISTRIB_01":
                events = gen.generate_distribution_scenario()
            elif args.scenario == "SC_CHAIN_01":
                events = gen.generate_chain_scenario()
            elif args.scenario == "SC_CIRCULAR_01":
                events = gen.generate_circular_scenario()
            elif args.scenario == "SC_LAYERED_01":
                events = gen.generate_layered_network_scenario()
            elif args.scenario == "all_scenarios":
                events.extend(gen.generate_funnel_scenario())
                events.extend(gen.generate_distribution_scenario())
                events.extend(gen.generate_chain_scenario())
                events.extend(gen.generate_circular_scenario())
                events.extend(gen.generate_layered_network_scenario())

            for ev in events:
                sink.write(ev)
                total_emitted += 1
                scenario_counts[ev.scenario_id] = scenario_counts.get(ev.scenario_id, 0) + 1

        else:
            # Continuous streaming generation
            next_tick = time.time()
            while True:
                now = time.time()
                if args.duration > 0 and (now - start_time) >= args.duration:
                    break

                batch = gen.generate_event_stream(
                    suspicious_rate=args.suspicious_rate, batch_size=1
                )
                for ev in batch:
                    sink.write(ev)
                    total_emitted += 1
                    scenario_counts[ev.scenario_id] = (
                        scenario_counts.get(ev.scenario_id, 0) + 1
                    )

                next_tick += interval
                sleep_dur = next_tick - time.time()
                if sleep_dur > 0:
                    time.sleep(sleep_dur)
                else:
                    next_tick = time.time()

    except KeyboardInterrupt:
        print("\n[*] Generator interrupted by user.")
    finally:
        sink.flush()
        sink.close()

    elapsed = max(0.001, time.time() - start_time)
    actual_tps = total_emitted / elapsed

    print("\n" + "=" * 70)
    print("  FinGraph Simulation Summary")
    print("=" * 70)
    print(f"  Total Transactions Generated: {total_emitted}")
    print(f"  Elapsed Time:                 {elapsed:.2f}s")
    print(f"  Throughput:                   {actual_tps:.2f} tx/sec")
    print("  Scenario Breakdown:")
    for sc, count in sorted(scenario_counts.items(), key=lambda x: -x[1]):
        pct = (count / total_emitted) * 100 if total_emitted > 0 else 0
        print(f"    - {sc:<25} : {count:>4} events ({pct:5.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    run_simulator()
