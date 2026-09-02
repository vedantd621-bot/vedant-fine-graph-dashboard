# FinGraph Security & Compliance Policy

## 1. Synthetic Data Guarantee
FinGraph strictly processes 100% synthetically generated financial transaction events. No real PII (Personally Identifiable Information), banking account numbers, real customer identities, or live financial infrastructure connections are permitted or utilized anywhere within this repository.

## 2. Secrets Management
- **No Hardcoded Credentials**: API secrets, database passwords, and SMTP credentials must strictly be injected via environment variables (`.env`).
- **Git Ignore**: `.env`, `*.pem`, `*.key`, and secret data are listed in `.gitignore`.
- **Default Development Passwords**: Documented credentials in `.env.example` and `docker-compose.yml` are clearly marked default placeholders for sandbox isolation only.

## 3. Cypher Injection Prevention
- All Cypher queries executed in backend services, Flink sinks, or migration scripts must strictly utilize parameterized inputs (e.g., `$account_id`, `$amount`).
- Dynamic string concatenation of user-supplied parameters into raw Cypher strings is strictly forbidden.

## 4. Simulated Freeze Action Safeguards
- The "Freeze Syndicate" UI action is an educational and portfolio demonstration feature.
- It performs an internal state update (`SET a.is_frozen = true`) in the local Neo4j database and logs a tamper-evident entry to the internal audit log.
- It has no external API integration with payment rails (Fedwire, ACH, SWIFT, SEPA).
