# FinGraph REST API Endpoint Reference

Detailed documentation of all REST endpoints exposed by the FinGraph FastAPI backend.

---

## 1. System Health

### `GET /health`
- **Description**: Returns general service liveness status.
- **Response**:
```json
{
  "status": "ok",
  "service": "fingraph-api"
}
```

### `GET /health/neo4j`
- **Description**: Verifies live graph database connectivity via Bolt driver.
- **Response (Healthy)**:
```json
{
  "status": "ok",
  "database": "neo4j",
  "message": "Connection healthy"
}
```

---

## 2. Fraud Alerts

### `GET /api/v1/alerts`
- **Parameters**: `severity`, `status`, `detection_type`, `risk_level`, `page`, `page_size`, `sort`, `order`.
- **Response**: `PaginatedResponse[AlertSummary]`

### `GET /api/v1/alerts/{alert_id}`
- **Parameters**: `alert_id`
- **Response**: `ApiResponse[AlertDetail]` (includes `evidence`, `reasons`, `related_accounts`, `transaction_ids`).

### `PATCH /api/v1/alerts/{alert_id}`
- **Request Body**:
```json
{
  "status": "INVESTIGATING",
  "notes": "Analyst review in progress"
}
```
- **Allowed States**: `OPEN`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`.
- **Response**: `ApiResponse[AlertDetail]`

---

## 3. Account Intelligence & Dossiers

### `GET /api/v1/accounts`
- **Parameters**: `risk_level`, `min_risk_score`, `max_risk_score`, `search`, `page`, `page_size`, `sort`, `order`.
- **Response**: `PaginatedResponse[AccountSummary]`

### `GET /api/v1/accounts/{account_id}`
- **Parameters**: `account_id`
- **Response**: `ApiResponse[AccountDetail]` (includes `features`, `rule_signals`, `risk_reasons`, `owner`, `bank`).

### `GET /api/v1/accounts/{account_id}/transactions`
- **Parameters**: `direction` (`INCOMING`/`OUTGOING`), `start_time`, `end_time`, `min_amount`, `max_amount`, `page`, `page_size`.
- **Response**: `PaginatedResponse[AccountTransactionItem]`

### `POST /api/v1/accounts/{account_id}/freeze`
- **Request Body**:
```json
{
  "freeze": true,
  "reason": "Simulated fraud containment freeze"
}
```
- **Response**: `ApiResponse[AccountFreezeResponse]`

---

## 4. Interactive Graph Visualizations

### `GET /api/v1/accounts/{account_id}/graph`
- **Parameters**: `depth` (1..3), `max_nodes` (10..200), `max_edges` (20..500).
- **Response**: `ApiResponse[GraphPayload]` (nodes with risk levels, directed edges with amounts and timestamps).

---

## 5. Forensic Investigation

### `GET /api/v1/investigation/money-trail`
- **Parameters**: `from_account`, `to_account`, `max_depth` (1..6), `start_time`, `end_time`.
- **Response**: `ApiResponse[List[MoneyTrailPath]]`

### `GET /api/v1/investigation/search`
- **Parameters**: `q` (search substring).
- **Response**: `ApiResponse[SearchResults]` (accounts, alerts, transaction IDs).

### `GET /api/v1/investigation/detections/{detection_id}`
- **Parameters**: `detection_id`
- **Response**: `ApiResponse[Dict]` (raw explainable detection object).

---

## 6. Executive & Operations Dashboard

### `GET /api/v1/dashboard/summary`
- **Response**: `ApiResponse[DashboardSummary]` (`total_accounts`, `total_transactions`, `open_alerts`, `total_transaction_volume`).

### `GET /api/v1/dashboard/risk-distribution`
- **Response**: `ApiResponse[RiskDistribution]` (counts across `low`, `medium`, `high`, `critical`).

### `GET /api/v1/dashboard/alert-trend`
- **Response**: `ApiResponse[List[AlertTrendPoint]]`

### `GET /api/v1/dashboard/top-risk-accounts`
- **Parameters**: `limit` (1..50)
- **Response**: `ApiResponse[List[AccountSummary]]`
