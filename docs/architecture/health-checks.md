# FinGraph Health Checks & Service Verification

This guide outlines verification endpoints and CLI commands to confirm the operating health of each subsystem.

## 1. System-Wide Health Status Matrix

| Component | Target Port | Health Check Mechanism | Expected Positive Response |
|---|---|---|---|
| **Kafka** | 9092 | `kafka-topics --bootstrap-server localhost:9092 --list` | List of topics (including `transactions`) |
| **Neo4j** | 7687 (Bolt) / 7474 (HTTP) | `cypher-shell -u neo4j -p password "RETURN 1;"` | `1` |
| **Flink** | 8081 | `GET http://localhost:8081/v1/overview` | `{"taskmanagers": ..., "slots-total": ...}` |
| **FastAPI Backend**| 8000 | `GET http://localhost:8000/api/health` | `{"status": "healthy", "neo4j": "connected"}` |
| **React Dashboard**| 3000 | `GET http://localhost:3000` | HTTP 200 OK |

## 2. API Health Check Specification

### Endpoint: `GET /api/health`
Returns the status of all internal service dependencies.

#### Sample Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-08-09T10:00:00Z",
  "components": {
    "neo4j": {
      "status": "connected",
      "latency_ms": 4.2
    },
    "kafka": {
      "status": "connected",
      "topic": "transactions"
    },
    "alert_engine": {
      "status": "active",
      "mode": "mock"
    }
  }
}
```
