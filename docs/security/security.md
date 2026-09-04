# FinGraph Security Architecture & Hardening Guide

## 1. Authentication & Session Management
- **RFC 7519 JSON Web Tokens (JWT)**: Cryptographically signed tokens with configurable expiration (default: 60 minutes).
- **Signature Algorithm**: HMAC-SHA256 (HS256) with minimum 32-byte secret enforcement.
- **Key Rotation**: Secrets configurable via JWT_SECRET_KEY environment variable without downtime.
- **Payload Claims**:
  - sub: Unique internal user ID (e.g. usr_admin_01)
  - username: Human operator identity
  - role: RBAC Role enum (ANALYST, INVESTIGATOR, ADMIN)
  - iat: Issued-at UTC timestamp
  - exp: Expiration UTC timestamp

## 2. Password Hashing & Secret Storage
- **Cryptographic Standard**: PBKDF2-HMAC-SHA256 conforming to NIST SP 800-132.
- **Key Derivation Work Factor**: 150,000 iterations.
- **Salt Generation**: Cryptographically secure 32-byte pseudo-random salt generated via secrets.token_bytes(32).
- **Constant-Time Verification**: hmac.compare_digest prevents timing side-channel attacks.

## 3. Role-Based Access Control (RBAC)
FinGraph enforces strict role segregation across all REST and WebSocket resources:

| Endpoint | Required Role | Description |
|---|---|---|
| POST /api/v1/auth/login | Public | Authenticates credentials & issues JWT |
| GET /api/v1/auth/me | ANALYST | Inspects active session details |
| GET /api/v1/dashboard/* | ANALYST | High-level KPI aggregations & risk distributions |
| GET /api/v1/alerts | ANALYST | Alert feed list & filters |
| GET /api/v1/alerts/{id} | ANALYST | Full alert dossier inspection |
| PATCH /api/v1/alerts/{id} | INVESTIGATOR | Alert state machine mutations |
| GET /api/v1/accounts | ANALYST | Account catalog & risk features |
| GET /api/v1/accounts/{id} | ANALYST | Detailed account graph dossier |
| POST /api/v1/accounts/{id}/freeze | INVESTIGATOR | Containment freeze action |
| GET /api/v1/investigation/* | ANALYST | Money trail & entity search |
| GET /api/v1/admin/* | ADMIN | User provisioning & audit trail logs |
| WS /api/v1/ws | ANALYST | Authenticated real-time streaming channel |

## 4. Alert State Machine Validation
Status transitions are strictly validated in the service layer:
- OPEN -> INVESTIGATING, RESOLVED, DISMISSED
- INVESTIGATING -> RESOLVED, DISMISSED
- RESOLVED & DISMISSED are terminal states.

## 5. Security Headers & Network Protections
The API injects defense-in-depth security response headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy: default-src 'self'
- Permissions-Policy: camera=(), microphone=(), geolocation=()
- X-Request-ID: Correlation ID (req_xxxxxxxxxxxx)
