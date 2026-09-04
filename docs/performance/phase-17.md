# FinGraph Phase 17 Performance Benchmark Report

**Environment**: Windows, Python 3.14.7  
**Benchmark Suite**: 100 Iterations per Operation  
**Target SLAs**: P95 < 25.0 ms, P99 < 50.0 ms  

---

## 1. Benchmark Results Summary

| Operation | P50 (ms) | P95 (ms) | P99 (ms) | Mean (ms) | StdDev (ms) | Min (ms) | Max (ms) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Detection Gap Discovery Scan** | 0.015 | 0.023 | 0.029 | 0.015 | 0.003 | 0.013 | 0.029 | **PASS** |
| **Adaptive Recommendation Synthesis** | 0.021 | 0.023 | 0.071 | 0.022 | 0.005 | 0.02 | 0.071 | **PASS** |
| **Shadow Detector Sandbox Simulation** | 0.008 | 0.01 | 0.042 | 0.009 | 0.004 | 0.008 | 0.042 | **PASS** |
| **Risk Score Outcome Calibration (5 Buckets)** | 0.021 | 0.031 | 0.062 | 0.023 | 0.007 | 0.02 | 0.062 | **PASS** |
| **Multi-Hop Threat Propagation (3 Hops & Topology)** | 0.053 | 0.067 | 0.173 | 0.056 | 0.013 | 0.051 | 0.173 | **PASS** |
| **Autonomous Intelligence Summary Aggregation** | 0.006 | 0.007 | 0.043 | 0.006 | 0.004 | 0.005 | 0.043 | **PASS** |

---

## 2. SLA Compliance

* **Autonomous Gap Scan SLA (<20ms)**: Observed P95 = **0.023 ms** (Exceeds SLA by 869.6x).
* **Adaptive Recommendation Synthesis SLA (<15ms)**: Observed P95 = **0.023 ms**.
* **Shadow Detector Simulation SLA (<30ms)**: Observed P95 = **0.01 ms**.
* **Risk Calibration Matrix SLA (<20ms)**: Observed P95 = **0.031 ms**.
* **Threat Propagation Analysis SLA (<25ms)**: Observed P95 = **0.067 ms**.
* **Zero Jitter / Stability**: Standard deviations across all 100-run trials remained under **0.013 ms**.
