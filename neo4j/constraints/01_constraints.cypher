// =============================================================================
// FinGraph: Neo4j Uniqueness Constraints
// Enforce primary key uniqueness and prevent duplicate node entities
// =============================================================================

// 1. Account uniqueness
CREATE CONSTRAINT c_account_id_unique IF NOT EXISTS
FOR (a:Account)
REQUIRE a.account_id IS UNIQUE;

// 2. Person uniqueness
CREATE CONSTRAINT c_person_id_unique IF NOT EXISTS
FOR (p:Person)
REQUIRE p.person_id IS UNIQUE;

// 3. Bank uniqueness
CREATE CONSTRAINT c_bank_id_unique IF NOT EXISTS
FOR (b:Bank)
REQUIRE b.bank_id IS UNIQUE;

// 4. Transaction uniqueness (if modeled as node or relationship property)
CREATE CONSTRAINT c_transaction_id_unique IF NOT EXISTS
FOR (t:Transaction)
REQUIRE t.transaction_id IS UNIQUE;
