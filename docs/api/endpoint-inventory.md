# FinGraph v1.0 REST API Endpoint Inventory

Complete registry of all 24 REST API routers and protected endpoints across the FinGraph platform.

---

## 1. Authentication & Security Endpoints (`/api/v1/auth`)

| Method | Endpoint | Role | Rate Limit | Description |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Public | 20 req/min | Authenticates user credentials and returns signed JWT access token |
| `POST` | `/api/v1/auth/logout` | Authenticated | 100 req/min | Invalidates active token session |
| `GET` | `/api/v1/auth/me` | Authenticated | 100 req/min | Returns current authenticated user dossier & permissions |

---

## 2. Autonomous Fraud Intelligence & Threat Propagation (`/api/v1/autonomous-intelligence`)

| Method | Endpoint | Role | Rate Limit | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/summary` | `ANALYST+` | 100 req/min | Executive autonomous discovery overview |
| `GET` | `/gaps` | `ANALYST+` | 100 req/min | List active graph detection gaps |
| `GET` | `/gaps/{gap_id}` | `ANALYST+` | 100 req/min | Retrieve detection gap telemetry & sample motifs |
| `POST` | `/gaps/scan` | `INVESTIGATOR+` | 30 req/min | Trigger on-demand graph gap scan |
| `GET` | `/recommendations` | `ANALYST+` | 100 req/min | List adaptive detector recommendations |
| `GET` | `/recommendations/{id}` | `ANALYST+` | 100 req/min | Get detector recommendation details |
| `POST` | `/recommendations/{id}/review`| `INVESTIGATOR` (Review) / `ADMIN` (Deploy) | 30 req/min | Human-in-the-loop review/approval gate |
| `GET` | `/detector-versions` | `ANALYST+` | 100 req/min | List immutable detector version history |
| `POST` | `/shadow/simulate` | `INVESTIGATOR+` | 20 req/min | Run non-destructive sandbox simulation |
| `GET` | `/shadow/simulations` | `ANALYST+` | 100 req/min | List historical shadow detector evaluations |
| `GET` | `/shadow/simulations/{id}` | `ANALYST+` | 100 req/min | Get single shadow simulation results |
| `GET` | `/risk-calibration` | `ANALYST+` | 100 req/min | 5-bucket empirical risk calibration report |
| `POST` | `/risk-calibration/refresh` | `INVESTIGATOR+` | 20 req/min | Refresh empirical risk calibration matrix |
| `POST` | `/threat-propagation/analyze` | `INVESTIGATOR+` | 30 req/min | Model multi-hop contagion spread |
| `GET` | `/threat-propagation/entities/{id}`| `ANALYST+` | 100 req/min | Fetch entity multi-hop contagion profile |

---

## 3. Advanced Graph Intelligence & Predictive Risk (`/api/v1/advanced-intelligence`)

| Method | Endpoint | Role | Rate Limit | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/networks/{id}/evolution` | `ANALYST+` | 100 req/min | Bounded snapshot evolution metrics |
| `GET` | `/networks/{id}/trajectory` | `ANALYST+` | 100 req/min | Risk momentum & velocity trajectory |
| `GET` | `/networks/{id}/forecast` | `ANALYST+` | 100 req/min | Multi-horizon risk forecasting (1h, 6h, 24h, 7d) |
| `GET` | `/entities/{type}/{id}/trajectory` | `ANALYST+` | 100 req/min | Entity-level risk trajectory |
| `GET` | `/emerging-networks` | `ANALYST+` | 100 req/min | Uncover rapidly forming syndicates |
| `GET` | `/early-warnings` | `ANALYST+` | 100 req/min | Proactive early warning list |
| `GET` | `/early-warnings/{id}` | `ANALYST+` | 100 req/min | Early warning details |
| `POST` | `/early-warnings/{id}/acknowledge` | `INVESTIGATOR+` | 50 req/min | Acknowledge early warning |
| `POST` | `/early-warnings/{id}/escalate` | `INVESTIGATOR+` | 50 req/min | Escalate warning to case |
| `POST` | `/early-warnings/{id}/dismiss` | `INVESTIGATOR+` | 50 req/min | Dismiss warning with audit note |
| `GET` | `/patterns` | `ANALYST+` | 100 req/min | Discovered structural fraud motifs |
| `GET` | `/patterns/{id}` | `ANALYST+` | 100 req/min | Pattern motif details |
| `GET` | `/patterns/{id}/similar` | `ANALYST+` | 100 req/min | Jaccard/topological pattern similarity |
| `GET` | `/threat-level` | `ANALYST+` | 100 req/min | Enterprise threat level index (0-100) |
| `GET` | `/threat-level/history` | `ANALYST+` | 100 req/min | Historical threat score timeline |
| `GET` | `/enterprise-forecast` | `ANALYST+` | 100 req/min | Enterprise threat score projections |
| `GET` | `/command-center/advanced-summary` | `ANALYST+` | 100 req/min | Executive summary rollup |

---

## 4. Case Intelligence & Cross-Case Collaboration (`/api/v1/case-intelligence`)

| Method | Endpoint | Role | Rate Limit | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/evidence-graph/{case_id}` | `ANALYST+` | 100 req/min | Subgraph evidence graph for case |
| `GET` | `/correlations/{case_id}` | `ANALYST+` | 100 req/min | Shared entity & device correlations |
| `GET` | `/campaigns` | `ANALYST+` | 100 req/min | List multi-case fraud campaigns |
| `GET` | `/campaigns/{id}` | `ANALYST+` | 100 req/min | Campaign dossier & member cases |
| `POST` | `/campaigns/discover` | `INVESTIGATOR+` | 20 req/min | Run campaign discovery algorithm |
| `POST` | `/campaigns/{id}/confirm` | `INVESTIGATOR+` | 30 req/min | Confirm suspected campaign |
| `POST` | `/campaigns/{id}/cases` | `INVESTIGATOR+` | 30 req/min | Link case to campaign |
| `GET` | `/cases/{id}/comments` | `ANALYST+` | 100 req/min | Fetch case collaboration comments |
| `POST` | `/cases/{id}/comments` | `INVESTIGATOR+` | 50 req/min | Post forensic comment |
| `GET` | `/cases/{id}/collaborators` | `ANALYST+` | 100 req/min | List assigned investigators |
| `POST` | `/cases/{id}/collaborators` | `INVESTIGATOR+` | 50 req/min | Add case collaborator |
| `DELETE` | `/cases/{id}/collaborators/{uid}` | `INVESTIGATOR+` | 50 req/min | Remove collaborator |
| `GET` | `/cases/{id}/activities` | `ANALYST+` | 100 req/min | Forensic audit timeline |
| `GET` | `/command-center/summary` | `ANALYST+` | 100 req/min | Command center rollup metrics |

---

## 5. Operations, Triage & Prioritization (`/api/v1/operations`, `/api/v1/alerts`)

| Method | Endpoint | Role | Rate Limit | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/alerts` | `ANALYST+` | 100 req/min | Paginated alerts query |
| `GET` | `/api/v1/alerts/{id}` | `ANALYST+` | 100 req/min | Single alert details & evidence |
| `GET` | `/api/v1/operations/queue` | `ANALYST+` | 100 req/min | Prioritized alert queue with SLA |
| `POST` | `/api/v1/operations/triage` | `INVESTIGATOR+` | 50 req/min | Submit alert triage decision |
| `POST` | `/api/v1/operations/assign` | `INVESTIGATOR+` | 50 req/min | Assign investigator to alert |
| `GET` | `/api/v1/operations/sla-status` | `ANALYST+` | 100 req/min | Real-time SLA breach monitoring |
| `GET` | `/api/v1/operations/workload` | `ANALYST+` | 100 req/min | Investigator capacity metrics |
| `GET` | `/api/v1/operations/dashboard` | `ANALYST+` | 100 req/min | Real-time operational KPI metrics |
