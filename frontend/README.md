# FinGraph React Investigation Workstation

Financial crime analytics and syndicate investigation frontend built with **React 18**, **TypeScript**, and **D3.js**.

## Features
- Executive KPI dashboard with risk distribution and alert feed
- Alerts catalog with multi-criteria filtering and status transitions
- Account dossier view with GDS metrics, transaction history, and simulated freeze
- Interactive D3 force-directed syndicate subgraph visualizer
- Multi-hop money trail tracer and universal cross-entity search

## Local Startup
```bash
npm install
npm run dev
```

Server starts at: `http://localhost:5173`
Connects to API at: `http://localhost:8000` (configurable via `VITE_API_BASE_URL` or `REACT_APP_API_BASE_URL`).
