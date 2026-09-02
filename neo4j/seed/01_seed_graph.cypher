// =============================================================================
// FinGraph: Baseline Deterministic Seed Graph for Local Testing
// =============================================================================

// Banks
MERGE (b1:Bank {bank_id: 'B01'}) ON CREATE SET b1.name = 'Apex Global Bank';
MERGE (b2:Bank {bank_id: 'B02'}) ON CREATE SET b2.name = 'Horizon Trust Bank';
MERGE (b3:Bank {bank_id: 'B03'}) ON CREATE SET b3.name = 'Pinnacle Credit Union';

// Normal Retail Entity
MERGE (p1:Person {person_id: 'P101'}) ON CREATE SET p1.name = 'Alice Johnson';
MERGE (a1:Account {account_id: 'A101'}) ON CREATE SET a1.account_type = 'checking', a1.risk_score = 12.0, a1.is_frozen = false;
MERGE (p1)-[:OWNS]->(a1);
MERGE (a1)-[:HOSTED_BY]->(b1);

MERGE (p2:Person {person_id: 'P102'}) ON CREATE SET p2.name = 'Bob Smith';
MERGE (a2:Account {account_id: 'A102'}) ON CREATE SET a2.account_type = 'checking', a2.risk_score = 15.0, a2.is_frozen = false;
MERGE (p2)-[:OWNS]->(a2);
MERGE (a2)-[:HOSTED_BY]->(b2);

// Normal Transfer
MERGE (a1)-[r1:TRANSFERRED_TO {transaction_id: 'TX_NORM_001'}]->(a2)
ON CREATE SET r1.amount = 150.0, r1.currency = 'USD', r1.timestamp = datetime('2026-08-01T10:00:00Z'), r1.scenario_id = 'SC_NORMAL';

// Suspicious Circular Syndicate (A201 -> A202 -> A203 -> A201)
MERGE (p201:Person {person_id: 'P201'}) ON CREATE SET p201.name = 'David Vance';
MERGE (a201:Account {account_id: 'A201'}) ON CREATE SET a201.account_type = 'shell_business', a201.risk_score = 85.0, a201.is_frozen = false;
MERGE (p201)-[:OWNS]->(a201);
MERGE (a201)-[:HOSTED_BY]->(b1);

MERGE (p202:Person {person_id: 'P202'}) ON CREATE SET p202.name = 'Elena Rostova';
MERGE (a202:Account {account_id: 'A202'}) ON CREATE SET a202.account_type = 'offshore', a202.risk_score = 88.0, a202.is_frozen = false;
MERGE (p202)-[:OWNS]->(a202);
MERGE (a202)-[:HOSTED_BY]->(b2);

MERGE (p203:Person {person_id: 'P203'}) ON CREATE SET p203.name = 'Frank Miller';
MERGE (a203:Account {account_id: 'A203'}) ON CREATE SET a203.account_type = 'intermediary', a203.risk_score = 92.0, a203.is_frozen = false;
MERGE (p203)-[:OWNS]->(a203);
MERGE (a203)-[:HOSTED_BY]->(b3);

MERGE (a201)-[rc1:TRANSFERRED_TO {transaction_id: 'TX_CYC_001'}]->(a202)
ON CREATE SET rc1.amount = 9900.0, rc1.currency = 'USD', rc1.timestamp = datetime('2026-08-01T12:00:00Z'), rc1.scenario_id = 'SC_CIRCULAR_01';

MERGE (a202)-[rc2:TRANSFERRED_TO {transaction_id: 'TX_CYC_002'}]->(a203)
ON CREATE SET rc2.amount = 9850.0, rc2.currency = 'USD', rc2.timestamp = datetime('2026-08-01T12:05:00Z'), rc2.scenario_id = 'SC_CIRCULAR_01';

MERGE (a203)-[rc3:TRANSFERRED_TO {transaction_id: 'TX_CYC_003'}]->(a201)
ON CREATE SET rc3.amount = 9800.0, rc3.currency = 'USD', rc3.timestamp = datetime('2026-08-01T12:10:00Z'), rc3.scenario_id = 'SC_CIRCULAR_01';
