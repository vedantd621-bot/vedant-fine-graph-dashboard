# FinGraph Real-Time WebSocket Protocol Reference

The **FinGraph Real-Time WebSocket Service** streams live fraud detection alerts, composite risk score transitions, settled transaction ingestion events, and graph neighborhood changes to connected dashboard clients without requiring page refreshes.

---

## 1. Connection Details

- **Primary Versioned URL**: `ws://localhost:8000/api/v1/ws`
- **Legacy Alias**: `ws://localhost:8000/ws`
- **Heartbeat Interval**: 30 seconds (`system.ping` / `system.pong`)
- **Max Concurrent Clients**: Configurable (`REALTIME_MAX_CLIENTS`, default: 100)

---

## 2. Event Envelope Structure

Every WebSocket message conforms to the standard `RealtimeEvent[T]` envelope:

```json
{
  "event": "alert.created",
  "event_id": "evt_a1b2c3d4e5f6",
  "timestamp": "2026-09-03T11:10:00.000000Z",
  "version": 1,
  "data": { ... }
}
```

---

## 3. Supported Event Types & Payloads

### `1. alert.created`
Emitted immediately when a new fraud syndicate pattern is detected by the Cypher detection engine.
```json
{
  "event": "alert.created",
  "event_id": "evt_0a1b2c3d4e5f",
  "timestamp": "2026-09-03T11:10:00Z",
  "version": 1,
  "data": {
    "alert_id": "ALT_FUN_001",
    "detection_type": "FUNNEL",
    "severity": "HIGH",
    "confidence": 0.95,
    "primary_account": "A005",
    "risk_score": 82.5,
    "risk_level": "CRITICAL",
    "status": "OPEN",
    "description": "Funnel smurfing pattern detected: 4 sources aggregate into A005 with rapid sweep to A006",
    "total_amount": 36000.0,
    "currency": "USD",
    "related_accounts": ["A001", "A002", "A003", "A004", "A006"]
  }
}
```

### `2. alert.updated`
Emitted when an alert lifecycle status is modified (e.g. `OPEN` $\to$ `INVESTIGATING` $\to$ `RESOLVED` / `DISMISSED`).
```json
{
  "event": "alert.updated",
  "event_id": "evt_1a2b3c4d5e6f",
  "timestamp": "2026-09-03T11:10:15Z",
  "version": 1,
  "data": {
    "alert_id": "ALT_FUN_001",
    "previous_status": "OPEN",
    "status": "INVESTIGATING",
    "updated_at": "2026-09-03T11:10:15Z",
    "notes": "Assigned to compliance officer"
  }
}
```

### `3. risk.updated`
Emitted when an account's composite risk score or risk band changes following graph feature recalculations.
```json
{
  "event": "risk.updated",
  "event_id": "evt_2a3b4c5d6e7f",
  "timestamp": "2026-09-03T11:10:30Z",
  "version": 1,
  "data": {
    "account_id": "A005",
    "previous_score": 52.0,
    "score": 78.4,
    "previous_level": "HIGH",
    "risk_level": "CRITICAL",
    "model_version": "rule-gds-v1",
    "reasons": [
      "Account functions as an intermediary aggregation mule in a structured funneling pattern.",
      "PageRank centrality is in the top 5% of all accounts."
    ],
    "calculated_at": "2026-09-03T11:10:30Z"
  }
}
```

### `4. transaction.created`
Emitted when a transaction event is consumed from the Kafka `transactions` stream.
```json
{
  "event": "transaction.created",
  "event_id": "evt_3a4b5c6d7e8f",
  "timestamp": "2026-09-03T11:10:45Z",
  "version": 1,
  "data": {
    "transaction_id": "TX_10001",
    "source_account": "A001",
    "destination_account": "A005",
    "amount": 9500.0,
    "currency": "USD",
    "timestamp": "2026-09-03T11:10:44Z",
    "scenario_id": "SC_FUNNEL_01",
    "channel": "online"
  }
}
```

### `5. graph.updated`
Emitted when an account's local topology changes (new transaction link, account frozen/unfrozen, community shift).
```json
{
  "event": "graph.updated",
  "event_id": "evt_4a5b6c7d8e9f",
  "timestamp": "2026-09-03T11:11:00Z",
  "version": 1,
  "data": {
    "account_id": "A005",
    "change_type": "ACCOUNT_FROZEN",
    "related_account_id": "A001",
    "timestamp": "2026-09-03T11:11:00Z"
  }
}
```

---

## 4. Client Actions (Inbound)

Clients can send JSON commands over the WebSocket connection:

1. **Ping**:
   ```json
   { "action": "ping" }
   ```
2. **Channel Subscription**:
   ```json
   { "action": "subscribe", "channels": ["alerts", "risk", "transactions"] }
   ```
3. **Watch Specific Account**:
   ```json
   { "action": "watch_account", "account_id": "A005" }
   ```
