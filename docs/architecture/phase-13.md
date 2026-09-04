# Phase 13 Architecture — Real-Time Fraud Operations & Alert Prioritization

## Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    FinGraph Phase 13 Architecture                                   |
+----------------------------------------------------------------------------------------------------+
                                      |
                     Detection Engine + GDS Risk + Network Intelligence
                                      |
                                      v
       +---------------------------------------------------------------+
       |             Alert Prioritization & SLA Engine                 |
       |  - 4-Factor Deterministic Priority Scoring (0-100) -> P0-P3  |
       |  - Dynamic SLA Calculation & Countdown (15m to 24h)           |
       |  - Fingerprint Deduplication & Graph Correlation              |
       +---------------------------------------------------------------+
                                      |
              +-----------------------+-----------------------+
              |                                               |
              v                                               v
+-----------------------------+               +-------------------------------+
|  Triage & Workflow Engine   |               |     Investigator Workload     |
| - 7-State Finite State Mach |               | - Real-time Workload Metrics  |
| - RBAC Guard (INVESTIGATOR) |               | - Active Queues & Case Loads  |
| - Audit Trail Logging       |               | - Operational Resolution Time |
+-----------------------------+               +-------------------------------+
              |                                               |
              +-----------------------+-----------------------+
                                      |
                                      v
+----------------------------------------------------------------------------------------------------+
|                           Operations & Notification Services                                       |
| - Multi-Entity Unified Search (Alerts, Cases, Accounts, Transactions, Networks, Investigators)     |
| - In-App Notification Center with Role Scoping & WebSocket push                                    |
| - Executive Summary KPIs, Time-Series Fraud Trends & Detector Performance Analytics                 |
+----------------------------------------------------------------------------------------------------+
                                      |
                                      v
+----------------------------------------------------------------------------------------------------+
|                 FastAPI Operations Endpoints & React Operations Workstation                        |
| - REST APIs: /api/v1/operations/* and /api/v1/notifications/*                                      |
| - React UI: AlertQueuePage, InvestigationOperationsPage, FraudOperationsDashboard, Notifications   |
+----------------------------------------------------------------------------------------------------+
```
