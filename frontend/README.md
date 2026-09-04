# FinGraph React Investigation Workstation

Financial crime analytics and syndicate investigation frontend built with **React 18**, **TypeScript**, and **D3.js**, powered by a persistent **WebSocket** live stream.

## Features
- **Real-Time WebSocket Integration**: Managed `FinGraphWebSocketClient` with exponential backoff reconnect, heartbeat ping/pong, and event deduplication
- **Live Stream Indicator**: `● LIVE STREAM`, `● RECONNECTING...`, `● OFFLINE` in top navigation
- **Floating Alert Toasts**: Non-intrusive popup on `alert.created` with direct 1-click investigation link
- **Live Notification Center**: Header drawer with unread counter badges and raw telemetry event feed
- **Executive KPI Dashboard**: Live-updating metrics, risk distribution, and alert stream
- **Alerts Catalog**: Real-time alert insertion and lifecycle status transitions
- **Account Dossiers**: Live risk score recalculations, explainable justifications, and dynamic subgraph reloads
- **Interactive D3 Network Visualizer**: Semantic node coloring, link weights, drag/zoom/pan, and focal neighborhood navigation
- **Multi-Hop Money Trail Tracer**: Universal cross-entity search and path explorer

## Local Startup
```bash
npm install
npm run dev
```

- Web App: `http://localhost:5173`
- API Backend: `http://localhost:8000` (configurable via `VITE_API_BASE_URL` or `REACT_APP_API_BASE_URL`)
- WebSocket Stream: `ws://localhost:8000/api/v1/ws` (configurable via `VITE_WS_URL`)
