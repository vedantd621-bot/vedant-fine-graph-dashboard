# FinGraph Frontend Real-Time Live Stream Architecture

The React Investigation Dashboard incorporates a managed WebSocket layer that receives live streaming events from FastAPI and updates UI views reactively without full page reloads.

---

## 1. Core Real-Time Components

### 1. `FinGraphWebSocketClient` (`src/realtime/websocket.ts`)
- **Singleton Connection**: Managed connection per browser session.
- **Exponential Backoff Reconnection**: $1\text{s}, 2\text{s}, 4\text{s}, 8\text{s}, \dots, 30\text{s}$ with $10\%$ random jitter.
- **Event Deduplication**: Bounded LRU window (500 event IDs) preventing duplicate toasts or alerts.
- **Automatic Heartbeat**: Responds to `system.ping` events automatically.

### 2. `RealtimeProvider` & `useRealtime` Hook (`src/realtime/RealtimeContext.tsx`)
- Provides `status` (`LIVE`, `CONNECTING`, `DISCONNECTED`).
- Exposes `recentEvents` history for analyst diagnostics.
- Manages `activeToast` queue for popup notifications.

### 3. `NotificationCenter` (`src/components/realtime/NotificationCenter.tsx`)
- Unread badge counter in top navbar.
- Dropdown panel showing live alerts and raw event telemetry stream.

### 4. `AlertToast` (`src/components/realtime/AlertToast.tsx`)
- High-priority floating alert notification card in the upper-right corner.
- Includes direct 1-click navigation to the alert dossier.

---

## 2. Live Page Behaviors

| Page | Handled Events | Reactive UI Effect |
|---|---|---|
| **Executive Overview** | `alert.created`, `transaction.created`, `risk.updated` | Live KPI increments, prepends recent alerts feed, updates top risk table. |
| **Alerts Catalog** | `alert.created`, `alert.updated` | Inserts new alert row into catalog table, live updates status cell. |
| **Alert Detail** | `alert.updated` | Updates investigation lifecycle status and timestamp in-place. |
| **Account Dossier** | `risk.updated`, `graph.updated`, `transaction.created` | Live updates risk score & reasons, live refreshes subgraph, appends transaction to timeline. |
