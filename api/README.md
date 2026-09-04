# FinGraph FastAPI & Real-Time Backend

The FastAPI REST and WebSocket service for the FinGraph real-time fraud syndicate platform.

## Features
- **Health & Connectivity Checks**: `/health`, `/health/neo4j`, `/health/realtime`
- **Real-Time WebSocket Stream**: `WS /api/v1/ws`, `WS /ws` (live alerts, risk updates, transactions, graph updates)
- **Asynchronous Event Bus**: `backend/app/realtime/event_bus.py`
- **WebSocket Connection Manager**: `backend/app/realtime/connection_manager.py` (heartbeat pings, subscription filtering, concurrency limits)
- **Kafka Real-Time Consumer**: `backend/app/realtime/kafka_consumer.py` (`fingraph-realtime-api` group)
- **Alert Lifecycle Management**: `/api/v1/alerts` (list, detail, status transitions)
- **Account Dossiers & Timelines**: `/api/v1/accounts` (features, reasons, transactions)
- **Interactive Bounded Neighborhood Graphs**: `/api/v1/accounts/{id}/graph`
- **Multi-Hop Forensic Money Trails**: `/api/v1/investigation/money-trail`
- **Executive Dashboard Aggregates**: `/api/v1/dashboard/summary`, `/api/v1/dashboard/risk-distribution`
- **Simulated Account Freeze**: `/api/v1/accounts/{id}/freeze`

## Run Local Server
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
# or via compatibility alias:
uvicorn api.src.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- WebSocket endpoint: `ws://localhost:8000/api/v1/ws`
