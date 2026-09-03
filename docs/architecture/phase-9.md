# FinGraph Architecture: Phase 9 — Real-Time Alerting & WebSocket Live Investigation

## 1. Overview & Objectives

Phase 9 transforms FinGraph from a pull-based investigation tool into a **real-time event-driven fraud surveillance platform**. When new transaction events arrive via Kafka or when detection engines identify new syndicate patterns, updates are broadcasted immediately over persistent WebSocket connections to all connected investigator dashboards.

```text
┌─────────────────────────────────────────────────────────────┐
│                 Phase 2 Simulator / Kafka                   │
│                (topic: transactions, alerts)                │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON Events
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             FastAPI Realtime Consumer & EventBus            │
│            (backend/app/realtime/event_bus.py)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Typed Envelopes
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              WebSocket Connection Manager                   │
│          (/api/v1/ws with subscription filtering)           │
└──────────────────────────────┬──────────────────────────────┘
                               │ Live WebSocket Stream
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          React 18 Dashboard & Notification Center           │
│     (Live KPIs, Alert Toasts, Reactive Graph Updates)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Key Architecture Components

1. **Typed Event Envelope (`RealtimeEvent[T]`)**:
   - Fields: `event`, `event_id`, `timestamp`, `version=1`, `data`.
   - 5 Domain Events: `alert.created`, `alert.updated`, `risk.updated`, `transaction.created`, `graph.updated`.
   - 2 System Events: `system.ping`, `system.pong`.

2. **Decoupled Asynchronous Event Bus (`EventBus`)**:
   - In-memory async pub/sub dispatcher with exception isolation and history buffer.

3. **Multi-Client Connection Manager (`WebSocketConnectionManager`)**:
   - Handles max client concurrency (100 clients).
   - Manages heartbeat pings (30s interval).
   - Safe broadcasts with automatic dead-socket eviction.

4. **Background Kafka Consumer (`RealtimeKafkaConsumer`)**:
   - Background streaming consumer for Kafka topic `transactions`.
   - Routes new transactions and topology updates onto the `EventBus`.

5. **React Real-Time Layer**:
   - Automatic reconnect with exponential backoff and jitter.
   - Client-side deduplication via LRU `event_id` cache.
   - Integrated floating `AlertToast` and `NotificationCenter` drawer.
   - Live KPI counters and reactive graph updates across dashboard views.
