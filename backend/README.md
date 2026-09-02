# FinGraph Backend API (FastAPI)

FastAPI REST API layer exposing graph queries, risk calculations, community detection results, alert feeds, and simulated freeze actions to the React investigation dashboard.

## Key Endpoints
- `GET /api/health`: Health status of Neo4j, Kafka, and Alert system.
- `GET /api/stats`: High-level KPI metrics (transactions processed, high-risk entities, syndicate counts).
- `GET /api/accounts`: Paginated account list with risk filtering.
- `GET /api/accounts/{account_id}`: Detailed entity profile and counterparties.
- `GET /api/accounts/{account_id}/network`: Subgraph topology for D3 force layout.
- `GET /api/communities`: Detected fraud syndicates and modularity groups.
- `GET /api/alerts`: Real-time and historical risk alerts.
- `POST /api/freeze-syndicate`: Simulated compliance hold action with audit logging.
- `GET /api/audit-log`: Immutable record of analyst investigation actions.

## Local Execution
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
