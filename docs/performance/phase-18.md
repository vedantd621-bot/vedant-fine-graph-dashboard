# FinGraph v1.0 Integrated Performance & Load Benchmark Report

**Environment**: Windows, Python 3.14.7  
**Benchmark Suites**: 100-Iteration Micro-Benchmarks & 10,000-Transaction End-to-End Workloads  
**Target SLAs**: Latency P95 < 25.0 ms, Pipeline Throughput > 5,000 ops/sec  

---

## 1. Integrated End-to-End Pipeline Performance

| Workload Batch | Total Time | Throughput | P50 Latency | P95 Latency | P99 Latency | Error Rate | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **100 Transactions** | 0.001 s | **94,661 ops/s** | 0.000 ms | 0.083 ms | 0.200 ms | 0.00% | **PASS** |
| **1,000 Transactions** | 0.009 s | **110,579 ops/s** | 0.000 ms | 0.074 ms | 0.099 ms | 0.00% | **PASS** |
| **10,000 Transactions** | 0.108 s | **92,863 ops/s** | 0.000 ms | 0.075 ms | 0.105 ms | 0.00% | **PASS** |

---

## 2. Micro-Benchmark Summary (100 Iterations)

| Component / Subsystem | P50 (ms) | P95 (ms) | P99 (ms) | Mean (ms) | Target SLA |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Detection Gap Discovery** | 0.015 | 0.023 | 0.029 | 0.016 | $< 20.0$ ms |
| **Adaptive Recommendation Synthesis** | 0.021 | 0.023 | 0.071 | 0.023 | $< 15.0$ ms |
| **Shadow Detector Simulation Sandbox** | 0.008 | 0.010 | 0.042 | 0.011 | $< 30.0$ ms |
| **Risk Score Outcome Calibration** | 0.021 | 0.031 | 0.062 | 0.024 | $< 20.0$ ms |
| **Multi-Hop Threat Propagation (3 Hops)** | 0.053 | 0.067 | 0.173 | 0.060 | $< 25.0$ ms |
| **Autonomous Executive Summary** | 0.006 | 0.007 | 0.043 | 0.009 | $< 10.0$ ms |
