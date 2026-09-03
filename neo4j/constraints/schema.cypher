// =============================================================================
// FinGraph: Neo4j Uniqueness Constraints (Idempotent)
// Prevents duplicate nodes and guarantees entity identity integrity
// =============================================================================

// 1. Account Entity Uniqueness
CREATE CONSTRAINT c_account_id_unique IF NOT EXISTS
FOR (a:Account)
REQUIRE a.account_id IS UNIQUE;

// 2. Person / Corporate Entity Uniqueness
CREATE CONSTRAINT c_person_id_unique IF NOT EXISTS
FOR (p:Person)
REQUIRE p.person_id IS UNIQUE;

// 3. Bank Institution Uniqueness
CREATE CONSTRAINT c_bank_id_unique IF NOT EXISTS
FOR (b:Bank)
REQUIRE b.bank_id IS UNIQUE;
