# FinGraph Data Model Specification

## 1. Graph Schema Overview

FinGraph represents financial entities as nodes and interactions as directed edges within Neo4j.

```mermaid
erDiagram
    PERSON ||--o{ OWNS : "OWNS"
    ACCOUNT ||--o{ TRANSFERRED_TO : "TRANSFERRED_TO"
    ACCOUNT ||--|| HOSTED_BY : "HOSTED_BY"

    PERSON {
        string person_id PK "Unique Person Identifier (e.g., P101)"
        string name "Full Name"
        datetime created_at "Creation timestamp"
    }

    ACCOUNT {
        string account_id PK "Unique Account Identifier (e.g., A101)"
        string account_type "checking | savings | shell_business | intermediary"
        float risk_score "Current calculated risk score (0.0 to 100.0)"
        int community_id "Louvain community / syndicate ID"
        float pagerank "PageRank centrality score"
        boolean is_frozen "Simulated compliance freeze flag"
    }

    BANK {
        string bank_id PK "Unique Bank Identifier (e.g., B01)"
        string name "Financial Institution Name"
        string country "Country Code (ISO 3166-1 alpha-2)"
    }

    TRANSFERRED_TO {
        string transaction_id PK "Unique Transaction ID (e.g., TX10001)"
        float amount "Transaction monetary amount (USD)"
        string currency "ISO 4217 Currency Code (e.g., USD)"
        datetime timestamp "Transaction event timestamp (ISO 8601)"
        string scenario_id "Synthetic scenario identifier (e.g., SC_NORMAL, SC_CIRCULAR_01)"
        datetime created_at "System ingestion timestamp"
    }
```

## 2. Event Payload Schema (JSON)

Every transaction emitted over Kafka and processed by Flink adheres to:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FinGraphTransactionEvent",
  "type": "object",
  "properties": {
    "transaction_id": { "type": "string", "pattern": "^TX[0-9A-Za-z_-]+$" },
    "timestamp": { "type": "string", "format": "date-time" },
    "from_account": { "type": "string", "minLength": 2 },
    "to_account": { "type": "string", "minLength": 2 },
    "amount": { "type": "number", "minimum": 0.01 },
    "currency": { "type": "string", "minLength": 3, "maxLength": 3 },
    "from_person": { "type": "string" },
    "to_person": { "type": "string" },
    "bank": { "type": "string" },
    "transaction_type": { "type": "string" },
    "scenario_id": { "type": "string" },
    "is_synthetic": { "type": "boolean", "default": true }
  },
  "required": [
    "transaction_id",
    "timestamp",
    "from_account",
    "to_account",
    "amount",
    "currency",
    "from_person",
    "to_person",
    "bank"
  ]
}
```
