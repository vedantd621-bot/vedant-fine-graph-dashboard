# Case Management & Investigation Lifecycle

## Case State Machine

Cases follow a strictly enforced state transition model:

```text
         ┌───────────────┐
         │     OPEN      │
         └───────┬───────┘
                 │
         ┌───────▼───────┐
   ┌────►│  IN_PROGRESS  │◄────┐
   │     └───────┬───────┘     │
   │             │             │
   │     ┌───────▼───────┐     │
   │     │   ESCALATED   │     │
   │     └───────┬───────┘     │
   │             │             │
   │     ┌───────▼───────┐     │
   └─────┤   RESOLVED    ├─────┘ (Reopen)
         └───────┬───────┘
                 │
         ┌───────▼───────┐
         │    CLOSED     │
         └───────────────┘
```

### Valid Transitions Table
| Current Status | Allowed Next States | Trigger / Role |
| :--- | :--- | :--- |
| **`OPEN`** | `IN_PROGRESS`, `ESCALATED`, `RESOLVED`, `CLOSED` | Assignment or Triage (Investigator/Admin) |
| **`IN_PROGRESS`** | `ESCALATED`, `RESOLVED`, `CLOSED` | Investigation Progression (Investigator/Admin) |
| **`ESCALATED`** | `IN_PROGRESS`, `RESOLVED`, `CLOSED` | Senior Review / SAR Referral (Admin) |
| **`RESOLVED`** | `CLOSED`, `IN_PROGRESS` (Reopen) | Verification / Compliance (Investigator/Admin) |
| **`CLOSED`** | None (Terminal) | Archival (Admin) |

---

## RBAC Permissions Matrix

| Operation | Required Role | Analyst Permitted |
| :--- | :--- | :--- |
| **Create Case** | `INVESTIGATOR`, `ADMIN` | ❌ (403 Forbidden) |
| **Update Status** | `INVESTIGATOR`, `ADMIN` | ❌ (403 Forbidden) |
| **Assign Investigator** | `INVESTIGATOR`, `ADMIN` | ❌ (403 Forbidden) |
| **Add Note** | `INVESTIGATOR`, `ADMIN` | ❌ (403 Forbidden) |
| **Attach Evidence** | `INVESTIGATOR`, `ADMIN` | ❌ (403 Forbidden) |
| **Link / Unlink Entities** | `INVESTIGATOR`, `ADMIN` | ❌ (403 Forbidden) |
| **List / View Cases** | `ANALYST`, `INVESTIGATOR`, `ADMIN` | ✅ (Read-Only) |
| **View Case Timeline** | `ANALYST`, `INVESTIGATOR`, `ADMIN` | ✅ (Read-Only) |

---

## Real-Time Event Broadcasts

Whenever a case is created or mutated, FinGraph dispatches typed real-time events over WebSocket:
- `case.created`: Sent upon new case initialization.
- `case.updated`: Sent on status transitions, note additions, or evidence attachment.
- `account.frozen`: Sent when account containment is toggled.
