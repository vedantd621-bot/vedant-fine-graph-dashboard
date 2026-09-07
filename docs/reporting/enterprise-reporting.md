# FinGraph Enterprise Reporting Center & Cryptographic Snapshots

---

## 1. Supported Report Types (8 Enterprise Formats)

| Report Type | Purpose | Intended Audience |
| :--- | :--- | :--- |
| `EXECUTIVE_FRAUD_REPORT` | High-level threat level, loss mitigation, and syndicate summaries | Board, C-Suite, Regulators |
| `FRAUD_NETWORK_REPORT` | Deep topological dossiers, Louvain community clusters, originators | Senior Investigators, Law Enforcement |
| `CAMPAIGN_REPORT` | Cross-case syndicate correlation and financial exposure aggregation | Fraud Operations Directors |
| `INVESTIGATION_REPORT` | Triage efficiency, SLA adherence, and team throughput | Operations Managers |
| `DETECTOR_PERFORMANCE_REPORT` | Precision proxy, false positive ratios, and Cypher rule drift | Detection Engineers |
| `OPERATIONS_REPORT` | Queue depth, investigator workload distribution, and breaches | Shift Supervisors |
| `RISK_REPORT` | Entity score distribution across Critical, High, Medium bands | Risk & Compliance Officers |
| `TENANT_POSTURE_REPORT` | Multi-tenant boundary compliance and audit log integrity | Internal Auditors |

---

## 2. Cryptographic Immutability (SHA-256)

Every generated report snapshot is immediately hashed using SHA-256 across its normalized JSON serialization. The resulting 64-character hexadecimal digest is stored in `ReportSnapshot.content_hash` and returned in the HTTP response header `X-Content-Hash-SHA256` for tamper verification.

---

## 3. Spreadsheet Formula Injection Protection (CWE-1236)

When exporting to CSV, all values are checked for dangerous spreadsheet calculation prefixes:
* Leading `=` (e.g. `=cmd|' /C calc'!A0`)
* Leading `+` (e.g. `+1+1`)
* Leading `-` (e.g. `-1-1`)
* Leading `@` (e.g. `@SUM(...)`)
* Leading horizontal tab (`\t`) or carriage return (`\r`)

Any string beginning with one of these characters is automatically prepended with a single quote (`'`), rendering it as inert literal text in Microsoft Excel, LibreOffice, and Google Sheets.
