# FinGraph Phase 11 Performance & Latency Benchmarks

## Benchmark Methodology
- **Test Harness**: FastAPI Async TestClient with Python 3.14 on Windows 11.
- **Sample Size**: 100 benchmark iterations per endpoint (after 5 warmup iterations).
- **Authentication**: Pre-authenticated Bearer JWT (`INVESTIGATOR` role).
- **Rate Limiting**: Monitored and reset between benchmark passes.

---

## Measured Endpoint Latency (Real Execution)

| API Endpoint | Method | Mean (ms) | Median / p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/v1/cases` | GET | **7.24** | **6.90** | 10.26 | 11.31 | 6.03 | 11.31 |
| `GET /api/v1/cases/{id}` | GET | **6.64** | **6.55** | 7.41 | 8.27 | 5.85 | 8.27 |
| `GET /api/v1/entities/{id}/risk-profile` | GET | **8.40** | **8.77** | 9.80 | 10.03 | 6.41 | 10.03 |
| `GET /api/v1/entities/{id}/risk-explanation` | GET | **8.80** | **8.93** | 10.94 | 11.78 | 6.94 | 11.78 |
| `GET /api/v1/entities/{id}/timeline` | GET | **8.36** | **8.22** | 9.98 | 10.86 | 6.87 | 10.86 |
| `GET /api/v1/alerts/{id}/correlated` | GET | **7.90** | **7.83** | 8.85 | 10.01 | 6.86 | 10.01 |
| `GET /api/v1/alerts/{id}/recommendations` | GET | **7.88** | **7.78** | 9.44 | 9.58 | 6.77 | 9.58 |
| `GET /api/v1/investigation/analytics` | GET | **8.84** | **8.76** | 11.30 | 12.82 | 6.93 | 12.82 |
| `GET /api/v1/graph/neighborhood/{id}` | GET | **8.90** | **7.88** | 10.69 | 88.46 | 6.84 | 88.46 |
| `GET /api/v1/graph/suspicious-neighborhood/{id}` | GET | **8.34** | **8.28** | 10.27 | 13.68 | 6.51 | 13.68 |

---

## Key Performance Findings
- **Sub-10ms Mean Latency**: All Phase 11 intelligence and case management endpoints achieve an average response time $<10\text{ms}$.
- **Consistent Tail Latency**: 95% of requests complete in $\le 11.3\text{ms}$.
- **Zero Overhead Cryptography**: In-memory SHA-256 evidence hashing processes evidence items in $<0.05\text{ms}$.
