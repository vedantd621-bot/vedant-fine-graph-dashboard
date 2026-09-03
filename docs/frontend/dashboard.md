# FinGraph Frontend Investigation Dashboard

The **FinGraph Dashboard** is a financial intelligence and fraud syndicate investigation workstation built with **React 18**, **TypeScript**, and **D3.js**.

---

## 1. Workstation Pages & Screens

### 1. Executive Overview (`/`)
- **Real-Time KPIs**: Open alerts, critical accounts count, monitored entity population, and settled settlement volume.
- **Risk Distribution Chart**: Proportional stacked visualizer representing account categorizations across LOW, MEDIUM, HIGH, and CRITICAL bands.
- **Top Risk Candidates Table**: Ranked accounts sorted by composite risk scores with direct one-click deep-dive links.
- **Topological Alert Feed**: Stream of detected syndicate anomalies (Funnels, Wash Trading Rings, Layering Hubs).

### 2. Alerts Catalog (`/alerts`)
- Multi-dimensional filtering by severity (LOW, MEDIUM, HIGH, CRITICAL) and investigation status (OPEN, INVESTIGATING, RESOLVED, DISMISSED).
- Instant search across alert IDs and primary accounts.

### 3. Alert Dossier & Lifecycle (`/alerts/:alertId`)
- Forensic pattern evidence display (metrics, thresholds, observed values, confidence).
- Explainable risk justification bullet points.
- Related syndicate accounts and involved transaction references.
- Interactive local subgraph visualization.
- Status transitions: `Mark Investigating`, `Resolve`, `Dismiss`.

### 4. Account Catalog (`/accounts`)
- Complete entity directory with ownership names, host banks, PageRank centrality scores, Louvain community group IDs, and freeze statuses.

### 5. Account Dossier & Transaction Timeline (`/accounts/:accountId`)
- Complete account profile with GDS metrics (PageRank, total degree, Louvain community, WCC).
- Explainable audit justifications explaining why an account is elevated risk.
- Interactive neighborhood graph with depth toggle (1 Hop / 2 Hops).
- Chronological transaction timeline showing incoming and outgoing counterparty transfers.
- Administrative **Simulated Account Freeze** toggle button.

### 6. Forensic Investigation & Money Trail (`/investigation`)
- **Multi-Hop Money Trail Tracer**: Traces direct fund routing paths ($A \to B \to C \to D$) with step-by-step transaction IDs, amounts, and hop counts.
- **Universal Entity Search**: Unified multi-entity search across accounts, transactions, and alert IDs.

---

## 2. Interactive D3 Graph Visualizer

- **Force-Directed Physics Layout**: `d3.forceSimulation` with node collision avoidance, charge repulsion, and link springs.
- **Node Semantics**:
  - `Account`: Colored by risk level (Rose for Critical, Amber for High, Indigo for Medium, Emerald for Low).
  - `Person`: Sky Blue (`#38bdf8`) with dashed `OWNS` relationships.
  - `Bank`: Purple (`#a855f7`) with `HOSTED_BY` relationships.
- **Interactions**:
  - Pan & smooth zoom ($0.2\times$ to $4.0\times$).
  - Node dragging with physics pinning.
  - Hover tooltip displaying entity attributes, risk score, and ownership.
  - Edge hover displaying transaction amount and currency.
  - Click node to navigate to account dossier.

---

## 3. Local Development

```bash
# Frontend dev server
cd frontend
npm install
npm run dev

# Starts on http://localhost:5173
```
