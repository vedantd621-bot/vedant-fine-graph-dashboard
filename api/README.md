# FinGraph FastAPI Backend

The FastAPI REST service for the FinGraph platform.

## Features
- Health and Neo4j connectivity checks (`/health`, `/health/neo4j`)
- Alert management and lifecycle updates (`/api/v1/alerts`)
- Account dossiers and transaction timelines (`/api/v1/accounts`)
- Interactive bounded neighborhood graphs (`/api/v1/accounts/{id}/graph`)
- Multi-hop forensic money trails (`/api/v1/investigation/money-trail`)
- Executive dashboard aggregates (`/api/v1/dashboard/summary`, `/api/v1/dashboard/risk-distribution`)
- Simulated account freeze actions (`/api/v1/accounts/{id}/freeze`)

## Run Local Server
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
