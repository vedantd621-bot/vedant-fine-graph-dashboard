# Cryptographic Evidence Management & Provenance

## Evidence Integrity Model

To guarantee tamper-proof audit trails for legal and regulatory compliance (e.g. SAR filings, court proceedings), all evidence attached to an investigation case is cryptographically sealed using SHA-256 digests:

$$\text{Integrity Hash} = \text{SHA-256}(\text{case\_id} \parallel \text{evidence\_type} \parallel \text{source\_reference} \parallel \text{JSON}(\text{payload}))$$

```python
# Canonical Hash Generation Logic
hash_raw = f"{case_id}:{evidence_type.value}:{source_ref}:{payload_canonical_json}"
integrity_hash = hashlib.sha256(hash_raw.encode("utf-8")).hexdigest()
```

---

## Supported Evidence Types

| Evidence Type | Description | Source Reference Format | Payload Structure |
| :--- | :--- | :--- | :--- |
| **`TRANSACTION`** | Raw transaction record | `TX_XXXXXXXX` | Amount, currency, timestamp, channel, counterparties |
| **`ACCOUNT`** | Account profile and GDS metrics | `ACC_XXXXXXXX` | PageRank, community ID, degree, ownership |
| **`GRAPH_PATH`** | Multi-hop directed subgraph | Path signature string | Array of node IDs and edge relationship attributes |
| **`DETECTOR_RESULT`** | Output of Cypher pattern detector | Detector fingerprint / ID | Confidence, rule parameters, matched subgraphs |
| **`RISK_FACTOR`** | Computed explainable risk signal | Risk factor code | Metric name, observed value, threshold, weight |
| **`NOTE`** | Investigator forensic observation | Note ID (`NOTE-XXX`) | Author, timestamp, content |
| **`EXTERNAL`** | External intelligence report | Document ID / URL | External provider reference, metadata |

---

## Chain of Custody

1. **Immutable Stamping**: Evidence records cannot be modified once appended.
2. **Actor Attribution**: Attached evidence records include the creator's username, user ID, and timestamp.
3. **Audit Trail Synchronization**: Every evidence operation logs an immutable record in the `AuditService`.
