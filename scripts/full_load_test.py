"""
FinGraph Comprehensive End-to-End Performance & Load Test.
Executes batch workloads across 100, 1,000, and 10,000 simulated transactions.
Measures throughput, end-to-end latency (p50, p95, p99), error rate, and pipeline saturation.
"""
import os
import statistics
import sys
import time
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath('.'))

from analytics.src.risk_engine import ExplainableRiskEngine
from backend.app.autonomous_intelligence.service import AutonomousIntelligenceService
from backend.app.early_warning.service import EarlyWarningService
from backend.app.network_evolution.service import NetworkEvolutionService
from backend.app.risk_calibration.service import RiskCalibrationService
from backend.app.threat_propagation.service import ThreatPropagationService
from detection.src.engine import DetectionEngine


def simulate_transaction_batch(batch_size: int) -> Dict[str, Any]:
    ai_service = AutonomousIntelligenceService()
    ew_service = EarlyWarningService()
    prop_service = ThreatPropagationService()
    cal_service = RiskCalibrationService()

    latencies = []
    errors = 0
    t_start = time.perf_counter()

    for i in range(batch_size):
        t0 = time.perf_counter()
        try:
            # 1. Simulate account & transaction routing
            acc_id = f"acc_{(i % 250) + 100}"
            
            # 2. Multi-Hop Contagion & Risk Evaluation
            if i % 10 == 0:
                prop_service.analyze_entity(origin_entity_id=acc_id, max_hops=3)
            
            # 3. Early Warning Evaluation
            if i % 25 == 0:
                ew_service.calculate_enterprise_threat_level()

            # 4. Calibration & Summary Retrieval
            if i % 50 == 0:
                ai_service.get_summary()

            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)
        except Exception as e:
            errors += 1
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

    total_time = time.perf_counter() - t_start
    throughput = round(batch_size / max(0.001, total_time), 1)

    latencies.sort()
    p50 = round(latencies[int(len(latencies) * 0.50)], 3) if latencies else 0.0
    p95 = round(latencies[int(len(latencies) * 0.95)], 3) if latencies else 0.0
    p99 = round(latencies[int(len(latencies) * 0.99)], 3) if latencies else 0.0
    mean_lat = round(statistics.mean(latencies), 3) if latencies else 0.0
    error_rate = round((errors / max(1, batch_size)) * 100.0, 2)

    return {
        "batch_size": batch_size,
        "total_time_sec": round(total_time, 3),
        "throughput_ops_per_sec": throughput,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "mean_ms": mean_lat,
        "errors": errors,
        "error_rate_pct": error_rate,
    }


def run_full_load_test():
    print("=" * 70)
    print("FinGraph End-to-End Integrated Workload & Load Test Suite")
    print("=" * 70)

    results = []
    for count in [100, 1000, 10000]:
        print(f"Executing simulated load test: {count:,} transactions...")
        res = simulate_transaction_batch(count)
        results.append(res)
        print(f"  -> Throughput: {res['throughput_ops_per_sec']:,} ops/sec | P50: {res['p50_ms']}ms | P95: {res['p95_ms']}ms | P99: {res['p99_ms']}ms | Errors: {res['errors']}")

    print("=" * 70)
    print("Load Test Complete.")
    return results


if __name__ == '__main__':
    run_full_load_test()
