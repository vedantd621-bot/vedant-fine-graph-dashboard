// =============================================================================
// FinGraph: Deterministic Baseline Seed Graph (Idempotent Cypher Migration)
// =============================================================================

// -----------------------------------------------------------------------------
// 1. Banks
// -----------------------------------------------------------------------------
MERGE (b1:Bank {bank_id: 'B01'}) ON CREATE SET b1.name = 'Apex Global Bank', b1.country = 'US', b1.routing_number = '021000021';
MERGE (b2:Bank {bank_id: 'B02'}) ON CREATE SET b2.name = 'Horizon Trust Bank', b2.country = 'GB', b2.routing_number = '021000089';
MERGE (b3:Bank {bank_id: 'B03'}) ON CREATE SET b3.name = 'Pinnacle Credit Union', b3.country = 'CH', b3.routing_number = '021000155';
MERGE (b4:Bank {bank_id: 'B04'}) ON CREATE SET b4.name = 'Sterling Standard Bank', b4.country = 'SG', b4.routing_number = '021000244';

// -----------------------------------------------------------------------------
// 2. People & Entities
// -----------------------------------------------------------------------------
MERGE (p01:Person {person_id: 'P001'}) ON CREATE SET p01.name = 'Alice Vance', p01.country = 'US';
MERGE (p02:Person {person_id: 'P002'}) ON CREATE SET p02.name = 'Bob Martinez', p02.country = 'US';
MERGE (p03:Person {person_id: 'P003'}) ON CREATE SET p03.name = 'Charlie Clark', p03.country = 'US';
MERGE (p04:Person {person_id: 'P004'}) ON CREATE SET p04.name = 'Diana Ross', p04.country = 'US';
MERGE (p05:Person {person_id: 'P005'}) ON CREATE SET p05.name = 'Evan Wright (Mule Broker)', p05.country = 'US';
MERGE (p06:Person {person_id: 'P006'}) ON CREATE SET p06.name = 'Apex Offshore Holdings Ltd', p06.country = 'CH';
MERGE (p07:Person {person_id: 'P007'}) ON CREATE SET p07.name = 'Global Pooling Corp', p07.country = 'GB';
MERGE (p08:Person {person_id: 'P008'}) ON CREATE SET p08.name = 'Hannah Abbott', p08.country = 'GB';
MERGE (p09:Person {person_id: 'P009'}) ON CREATE SET p09.name = 'Ian Malcolm', p09.country = 'GB';
MERGE (p10:Person {person_id: 'P010'}) ON CREATE SET p10.name = 'Venture Syndicate Master', p10.country = 'US';
MERGE (p11:Person {person_id: 'P011'}) ON CREATE SET p11.name = 'Jack Napier', p11.country = 'US';
MERGE (p12:Person {person_id: 'P012'}) ON CREATE SET p12.name = 'Karen Page', p12.country = 'US';
MERGE (p13:Person {person_id: 'P013'}) ON CREATE SET p13.name = 'Liam Neeson', p13.country = 'US';
MERGE (p14:Person {person_id: 'P014'}) ON CREATE SET p14.name = 'Mia Wallace', p14.country = 'US';
MERGE (p15:Person {person_id: 'P015'}) ON CREATE SET p15.name = 'Noah Bennett', p15.country = 'US';
MERGE (p16:Person {person_id: 'P016'}) ON CREATE SET p16.name = 'Olivia Dunham', p16.country = 'US';
MERGE (p17:Person {person_id: 'P017'}) ON CREATE SET p17.name = 'Peter Bishop', p17.country = 'US';
MERGE (p18:Person {person_id: 'P018'}) ON CREATE SET p18.name = 'Apex Corporate Payroll', p18.country = 'US';
MERGE (p19:Person {person_id: 'P019'}) ON CREATE SET p19.name = 'Metro Retail Merchant LLC', p19.country = 'US';
MERGE (p20:Person {person_id: 'P020'}) ON CREATE SET p20.name = 'National Power & Electric', p20.country = 'US';
MERGE (p21:Person {person_id: 'P021'}) ON CREATE SET p21.name = 'Quentin Coldwater', p21.country = 'US';
MERGE (p22:Person {person_id: 'P022'}) ON CREATE SET p22.name = 'Rachel Green', p22.country = 'US';
MERGE (p23:Person {person_id: 'P023'}) ON CREATE SET p23.name = 'Steve Rogers', p23.country = 'US';
MERGE (p24:Person {person_id: 'P024'}) ON CREATE SET p24.name = 'Tony Stark Intermediary', p24.country = 'US';
MERGE (p25:Person {person_id: 'P025'}) ON CREATE SET p25.name = 'Ursula K. Le Guin', p25.country = 'US';

// -----------------------------------------------------------------------------
// 3. Accounts, Ownerships, and Host Banks
// -----------------------------------------------------------------------------
MERGE (a01:Account {account_id: 'A001'}) ON CREATE SET a01.account_type = 'checking', a01.risk_score = 12.0, a01.is_frozen = false;
MERGE (p01)-[:OWNS]->(a01); MERGE (a01)-[:HOSTED_BY]->(b1);

MERGE (a02:Account {account_id: 'A002'}) ON CREATE SET a02.account_type = 'checking', a02.risk_score = 15.0, a02.is_frozen = false;
MERGE (p02)-[:OWNS]->(a02); MERGE (a02)-[:HOSTED_BY]->(b1);

MERGE (a03:Account {account_id: 'A003'}) ON CREATE SET a03.account_type = 'savings', a03.risk_score = 10.0, a03.is_frozen = false;
MERGE (p03)-[:OWNS]->(a03); MERGE (a03)-[:HOSTED_BY]->(b2);

MERGE (a04:Account {account_id: 'A004'}) ON CREATE SET a04.account_type = 'checking', a04.risk_score = 14.0, a04.is_frozen = false;
MERGE (p04)-[:OWNS]->(a04); MERGE (a04)-[:HOSTED_BY]->(b2);

MERGE (a05:Account {account_id: 'A005'}) ON CREATE SET a05.account_type = 'intermediary', a05.risk_score = 78.0, a05.is_frozen = false;
MERGE (p05)-[:OWNS]->(a05); MERGE (a05)-[:HOSTED_BY]->(b1);

MERGE (a06:Account {account_id: 'A006'}) ON CREATE SET a06.account_type = 'offshore', a06.risk_score = 85.0, a06.is_frozen = false;
MERGE (p06)-[:OWNS]->(a06); MERGE (a06)-[:HOSTED_BY]->(b3);

MERGE (a07:Account {account_id: 'A007'}) ON CREATE SET a07.account_type = 'shell_business', a07.risk_score = 88.0, a07.is_frozen = false;
MERGE (p07)-[:OWNS]->(a07); MERGE (a07)-[:HOSTED_BY]->(b2);

MERGE (a08:Account {account_id: 'A008'}) ON CREATE SET a08.account_type = 'checking', a08.risk_score = 35.0, a08.is_frozen = false;
MERGE (p08)-[:OWNS]->(a08); MERGE (a08)-[:HOSTED_BY]->(b2);

MERGE (a09:Account {account_id: 'A009'}) ON CREATE SET a09.account_type = 'checking', a09.risk_score = 35.0, a09.is_frozen = false;
MERGE (p09)-[:OWNS]->(a09); MERGE (a09)-[:HOSTED_BY]->(b2);

MERGE (a10:Account {account_id: 'A010'}) ON CREATE SET a10.account_type = 'business', a10.risk_score = 75.0, a10.is_frozen = false;
MERGE (p10)-[:OWNS]->(a10); MERGE (a10)-[:HOSTED_BY]->(b1);

MERGE (a11:Account {account_id: 'A011'}) ON CREATE SET a11.account_type = 'checking', a11.risk_score = 25.0, a11.is_frozen = false;
MERGE (p11)-[:OWNS]->(a11); MERGE (a11)-[:HOSTED_BY]->(b1);

MERGE (a12:Account {account_id: 'A012'}) ON CREATE SET a12.account_type = 'checking', a12.risk_score = 25.0, a12.is_frozen = false;
MERGE (p12)-[:OWNS]->(a12); MERGE (a12)-[:HOSTED_BY]->(b1);

MERGE (a13:Account {account_id: 'A013'}) ON CREATE SET a13.account_type = 'checking', a13.risk_score = 25.0, a13.is_frozen = false;
MERGE (p13)-[:OWNS]->(a13); MERGE (a13)-[:HOSTED_BY]->(b4);

MERGE (a14:Account {account_id: 'A014'}) ON CREATE SET a14.account_type = 'checking', a14.risk_score = 25.0, a14.is_frozen = false;
MERGE (p14)-[:OWNS]->(a14); MERGE (a14)-[:HOSTED_BY]->(b4);

MERGE (a15:Account {account_id: 'A015'}) ON CREATE SET a15.account_type = 'checking', a15.risk_score = 25.0, a15.is_frozen = false;
MERGE (p15)-[:OWNS]->(a15); MERGE (a15)-[:HOSTED_BY]->(b4);

MERGE (a16:Account {account_id: 'A016'}) ON CREATE SET a16.account_type = 'intermediary', a16.risk_score = 65.0, a16.is_frozen = false;
MERGE (p16)-[:OWNS]->(a16); MERGE (a16)-[:HOSTED_BY]->(b2);

MERGE (a17:Account {account_id: 'A017'}) ON CREATE SET a17.account_type = 'intermediary', a17.risk_score = 65.0, a17.is_frozen = false;
MERGE (p17)-[:OWNS]->(a17); MERGE (a17)-[:HOSTED_BY]->(b2);

MERGE (a18:Account {account_id: 'A018'}) ON CREATE SET a18.account_type = 'business', a18.risk_score = 5.0, a18.is_frozen = false;
MERGE (p18)-[:OWNS]->(a18); MERGE (a18)-[:HOSTED_BY]->(b1);

MERGE (a19:Account {account_id: 'A019'}) ON CREATE SET a19.account_type = 'business', a19.risk_score = 8.0, a19.is_frozen = false;
MERGE (p19)-[:OWNS]->(a19); MERGE (a19)-[:HOSTED_BY]->(b1);

MERGE (a20:Account {account_id: 'A020'}) ON CREATE SET a20.account_type = 'business', a20.risk_score = 4.0, a20.is_frozen = false;
MERGE (p20)-[:OWNS]->(a20); MERGE (a20)-[:HOSTED_BY]->(b1);

MERGE (a21:Account {account_id: 'A021'}) ON CREATE SET a21.account_type = 'intermediary', a21.risk_score = 60.0, a21.is_frozen = false;
MERGE (p21)-[:OWNS]->(a21); MERGE (a21)-[:HOSTED_BY]->(b2);

MERGE (a22:Account {account_id: 'A022'}) ON CREATE SET a22.account_type = 'intermediary', a22.risk_score = 65.0, a22.is_frozen = false;
MERGE (p22)-[:OWNS]->(a22); MERGE (a22)-[:HOSTED_BY]->(b3);

MERGE (a23:Account {account_id: 'A023'}) ON CREATE SET a23.account_type = 'intermediary', a23.risk_score = 70.0, a23.is_frozen = false;
MERGE (p23)-[:OWNS]->(a23); MERGE (a23)-[:HOSTED_BY]->(b3);

MERGE (a24:Account {account_id: 'A024'}) ON CREATE SET a24.account_type = 'offshore', a24.risk_score = 75.0, a24.is_frozen = false;
MERGE (p24)-[:OWNS]->(a24); MERGE (a24)-[:HOSTED_BY]->(b4);

MERGE (a25:Account {account_id: 'A025'}) ON CREATE SET a25.account_type = 'shell_business', a25.risk_score = 92.0, a25.is_frozen = false;
MERGE (p25)-[:OWNS]->(a25); MERGE (a25)-[:HOSTED_BY]->(b1);

MERGE (a26:Account {account_id: 'A026'}) ON CREATE SET a26.account_type = 'shell_business', a26.risk_score = 90.0, a26.is_frozen = false;
MERGE (p01)-[:OWNS]->(a26); MERGE (a26)-[:HOSTED_BY]->(b2);

MERGE (a27:Account {account_id: 'A027'}) ON CREATE SET a27.account_type = 'shell_business', a27.risk_score = 91.0, a27.is_frozen = false;
MERGE (p02)-[:OWNS]->(a27); MERGE (a27)-[:HOSTED_BY]->(b3);

MERGE (a28:Account {account_id: 'A028'}) ON CREATE SET a28.account_type = 'checking', a28.risk_score = 45.0, a28.is_frozen = false;
MERGE (p03)-[:OWNS]->(a28); MERGE (a28)-[:HOSTED_BY]->(b1);

MERGE (a29:Account {account_id: 'A029'}) ON CREATE SET a29.account_type = 'checking', a29.risk_score = 45.0, a29.is_frozen = false;
MERGE (p04)-[:OWNS]->(a29); MERGE (a29)-[:HOSTED_BY]->(b2);

MERGE (a30:Account {account_id: 'A030'}) ON CREATE SET a30.account_type = 'savings', a30.risk_score = 15.0, a30.is_frozen = false;
MERGE (p05)-[:OWNS]->(a30); MERGE (a30)-[:HOSTED_BY]->(b4);

// -----------------------------------------------------------------------------
// 4. Normal Transactions
// -----------------------------------------------------------------------------
MATCH (src:Account {account_id: 'A018'}), (dst:Account {account_id: 'A001'})
MERGE (src)-[r:TRANSFERRED_TO {transaction_id: 'TX_NORM_001'}]->(dst)
ON CREATE SET r.amount = 4500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-01T09:00:00Z'), r.scenario_id = 'SC_NORMAL', r.transaction_type = 'salary', r.channel = 'wire';

MATCH (src:Account {account_id: 'A018'}), (dst:Account {account_id: 'A002'})
MERGE (src)-[r:TRANSFERRED_TO {transaction_id: 'TX_NORM_002'}]->(dst)
ON CREATE SET r.amount = 5200.0, r.currency = 'USD', r.timestamp = datetime('2026-08-01T09:05:00Z'), r.scenario_id = 'SC_NORMAL', r.transaction_type = 'salary', r.channel = 'wire';

MATCH (src:Account {account_id: 'A001'}), (dst:Account {account_id: 'A019'})
MERGE (src)-[r:TRANSFERRED_TO {transaction_id: 'TX_NORM_003'}]->(dst)
ON CREATE SET r.amount = 85.50, r.currency = 'USD', r.timestamp = datetime('2026-08-02T14:30:00Z'), r.scenario_id = 'SC_NORMAL', r.transaction_type = 'purchase', r.channel = 'pos';

MATCH (src:Account {account_id: 'A002'}), (dst:Account {account_id: 'A019'})
MERGE (src)-[r:TRANSFERRED_TO {transaction_id: 'TX_NORM_004'}]->(dst)
ON CREATE SET r.amount = 120.00, r.currency = 'USD', r.timestamp = datetime('2026-08-02T15:00:00Z'), r.scenario_id = 'SC_NORMAL', r.transaction_type = 'purchase', r.channel = 'pos';

MATCH (src:Account {account_id: 'A001'}), (dst:Account {account_id: 'A002'})
MERGE (src)-[r:TRANSFERRED_TO {transaction_id: 'TX_NORM_005'}]->(dst)
ON CREATE SET r.amount = 150.00, r.currency = 'USD', r.timestamp = datetime('2026-08-03T18:00:00Z'), r.scenario_id = 'SC_NORMAL', r.transaction_type = 'transfer', r.channel = 'mobile';

MATCH (src:Account {account_id: 'A002'}), (dst:Account {account_id: 'A020'})
MERGE (src)-[r:TRANSFERRED_TO {transaction_id: 'TX_NORM_006'}]->(dst)
ON CREATE SET r.amount = 240.00, r.currency = 'USD', r.timestamp = datetime('2026-08-04T10:00:00Z'), r.scenario_id = 'SC_NORMAL', r.transaction_type = 'bill_payment', r.channel = 'online';

// -----------------------------------------------------------------------------
// 5. Pattern A: Funnel / Smurfing (SC_FUNNEL_01)
// -----------------------------------------------------------------------------
MATCH (s1:Account {account_id: 'A001'}), (m:Account {account_id: 'A005'})
MERGE (s1)-[r:TRANSFERRED_TO {transaction_id: 'TX_FUN_001'}]->(m)
ON CREATE SET r.amount = 8500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-05T10:00:00Z'), r.scenario_id = 'SC_FUNNEL_01', r.transaction_type = 'smurfing', r.channel = 'online';

MATCH (s2:Account {account_id: 'A002'}), (m:Account {account_id: 'A005'})
MERGE (s2)-[r:TRANSFERRED_TO {transaction_id: 'TX_FUN_002'}]->(m)
ON CREATE SET r.amount = 9200.0, r.currency = 'USD', r.timestamp = datetime('2026-08-05T10:15:00Z'), r.scenario_id = 'SC_FUNNEL_01', r.transaction_type = 'smurfing', r.channel = 'online';

MATCH (s3:Account {account_id: 'A003'}), (m:Account {account_id: 'A005'})
MERGE (s3)-[r:TRANSFERRED_TO {transaction_id: 'TX_FUN_003'}]->(m)
ON CREATE SET r.amount = 8900.0, r.currency = 'USD', r.timestamp = datetime('2026-08-05T10:30:00Z'), r.scenario_id = 'SC_FUNNEL_01', r.transaction_type = 'smurfing', r.channel = 'online';

MATCH (s4:Account {account_id: 'A004'}), (m:Account {account_id: 'A005'})
MERGE (s4)-[r:TRANSFERRED_TO {transaction_id: 'TX_FUN_004'}]->(m)
ON CREATE SET r.amount = 9400.0, r.currency = 'USD', r.timestamp = datetime('2026-08-05T10:45:00Z'), r.scenario_id = 'SC_FUNNEL_01', r.transaction_type = 'smurfing', r.channel = 'online';

MATCH (m:Account {account_id: 'A005'}), (d:Account {account_id: 'A006'})
MERGE (m)-[r:TRANSFERRED_TO {transaction_id: 'TX_FUN_005'}]->(d)
ON CREATE SET r.amount = 35280.0, r.currency = 'USD', r.timestamp = datetime('2026-08-05T12:00:00Z'), r.scenario_id = 'SC_FUNNEL_01', r.transaction_type = 'pass_through', r.channel = 'wire';

// -----------------------------------------------------------------------------
// 6. Pattern B: One-to-Many Distribution (SC_DISTRIB_01)
// -----------------------------------------------------------------------------
MATCH (s:Account {account_id: 'A010'}), (d1:Account {account_id: 'A011'})
MERGE (s)-[r:TRANSFERRED_TO {transaction_id: 'TX_DIS_001'}]->(d1)
ON CREATE SET r.amount = 7500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-06T08:00:00Z'), r.scenario_id = 'SC_DISTRIB_01', r.transaction_type = 'dispersion', r.channel = 'wire';

MATCH (s:Account {account_id: 'A010'}), (d2:Account {account_id: 'A012'})
MERGE (s)-[r:TRANSFERRED_TO {transaction_id: 'TX_DIS_002'}]->(d2)
ON CREATE SET r.amount = 7500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-06T08:05:00Z'), r.scenario_id = 'SC_DISTRIB_01', r.transaction_type = 'dispersion', r.channel = 'wire';

MATCH (s:Account {account_id: 'A010'}), (d3:Account {account_id: 'A013'})
MERGE (s)-[r:TRANSFERRED_TO {transaction_id: 'TX_DIS_003'}]->(d3)
ON CREATE SET r.amount = 7500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-06T08:10:00Z'), r.scenario_id = 'SC_DISTRIB_01', r.transaction_type = 'dispersion', r.channel = 'wire';

MATCH (s:Account {account_id: 'A010'}), (d4:Account {account_id: 'A014'})
MERGE (s)-[r:TRANSFERRED_TO {transaction_id: 'TX_DIS_004'}]->(d4)
ON CREATE SET r.amount = 7500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-06T08:15:00Z'), r.scenario_id = 'SC_DISTRIB_01', r.transaction_type = 'dispersion', r.channel = 'wire';

MATCH (s:Account {account_id: 'A010'}), (d5:Account {account_id: 'A015'})
MERGE (s)-[r:TRANSFERRED_TO {transaction_id: 'TX_DIS_005'}]->(d5)
ON CREATE SET r.amount = 7500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-06T08:20:00Z'), r.scenario_id = 'SC_DISTRIB_01', r.transaction_type = 'dispersion', r.channel = 'wire';

// -----------------------------------------------------------------------------
// 7. Pattern C: Intermediary Chain (SC_CHAIN_01)
// -----------------------------------------------------------------------------
MATCH (c1:Account {account_id: 'A020'}), (c2:Account {account_id: 'A021'})
MERGE (c1)-[r:TRANSFERRED_TO {transaction_id: 'TX_CHN_001'}]->(c2)
ON CREATE SET r.amount = 35000.0, r.currency = 'USD', r.timestamp = datetime('2026-08-07T11:00:00Z'), r.scenario_id = 'SC_CHAIN_01', r.transaction_type = 'pass_through', r.channel = 'online';

MATCH (c2:Account {account_id: 'A021'}), (c3:Account {account_id: 'A022'})
MERGE (c2)-[r:TRANSFERRED_TO {transaction_id: 'TX_CHN_002'}]->(c3)
ON CREATE SET r.amount = 34300.0, r.currency = 'USD', r.timestamp = datetime('2026-08-07T11:30:00Z'), r.scenario_id = 'SC_CHAIN_01', r.transaction_type = 'pass_through', r.channel = 'online';

MATCH (c3:Account {account_id: 'A022'}), (c4:Account {account_id: 'A023'})
MERGE (c3)-[r:TRANSFERRED_TO {transaction_id: 'TX_CHN_003'}]->(c4)
ON CREATE SET r.amount = 33600.0, r.currency = 'USD', r.timestamp = datetime('2026-08-07T12:00:00Z'), r.scenario_id = 'SC_CHAIN_01', r.transaction_type = 'pass_through', r.channel = 'online';

MATCH (c4:Account {account_id: 'A023'}), (c5:Account {account_id: 'A024'})
MERGE (c4)-[r:TRANSFERRED_TO {transaction_id: 'TX_CHN_004'}]->(c5)
ON CREATE SET r.amount = 32900.0, r.currency = 'USD', r.timestamp = datetime('2026-08-07T12:30:00Z'), r.scenario_id = 'SC_CHAIN_01', r.transaction_type = 'pass_through', r.channel = 'online';

// -----------------------------------------------------------------------------
// 8. Pattern D: Circular Flow (SC_CIRCULAR_01)
// -----------------------------------------------------------------------------
MATCH (r1:Account {account_id: 'A025'}), (r2:Account {account_id: 'A026'})
MERGE (r1)-[r:TRANSFERRED_TO {transaction_id: 'TX_CYC_001'}]->(r2)
ON CREATE SET r.amount = 24000.0, r.currency = 'USD', r.timestamp = datetime('2026-08-08T14:00:00Z'), r.scenario_id = 'SC_CIRCULAR_01', r.transaction_type = 'circular', r.channel = 'wire';

MATCH (r2:Account {account_id: 'A026'}), (r3:Account {account_id: 'A027'})
MERGE (r2)-[r:TRANSFERRED_TO {transaction_id: 'TX_CYC_002'}]->(r3)
ON CREATE SET r.amount = 23750.0, r.currency = 'USD', r.timestamp = datetime('2026-08-08T14:15:00Z'), r.scenario_id = 'SC_CIRCULAR_01', r.transaction_type = 'circular', r.channel = 'wire';

MATCH (r3:Account {account_id: 'A027'}), (r1:Account {account_id: 'A025'})
MERGE (r3)-[r:TRANSFERRED_TO {transaction_id: 'TX_CYC_003'}]->(r1)
ON CREATE SET r.amount = 23500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-08T14:30:00Z'), r.scenario_id = 'SC_CIRCULAR_01', r.transaction_type = 'circular', r.channel = 'wire';

// -----------------------------------------------------------------------------
// 9. Pattern E: Layered Network (SC_LAYERED_01)
// -----------------------------------------------------------------------------
MATCH (l1a:Account {account_id: 'A028'}), (l2a:Account {account_id: 'A016'})
MERGE (l1a)-[r:TRANSFERRED_TO {transaction_id: 'TX_LAY_001'}]->(l2a)
ON CREATE SET r.amount = 9000.0, r.currency = 'USD', r.timestamp = datetime('2026-08-09T09:00:00Z'), r.scenario_id = 'SC_LAYERED_01', r.transaction_type = 'layering', r.channel = 'online';

MATCH (l1b:Account {account_id: 'A029'}), (l2b:Account {account_id: 'A017'})
MERGE (l1b)-[r:TRANSFERRED_TO {transaction_id: 'TX_LAY_002'}]->(l2b)
ON CREATE SET r.amount = 9000.0, r.currency = 'USD', r.timestamp = datetime('2026-08-09T09:10:00Z'), r.scenario_id = 'SC_LAYERED_01', r.transaction_type = 'layering', r.channel = 'online';

MATCH (l2a:Account {account_id: 'A016'}), (l3:Account {account_id: 'A007'})
MERGE (l2a)-[r:TRANSFERRED_TO {transaction_id: 'TX_LAY_003'}]->(l3)
ON CREATE SET r.amount = 8800.0, r.currency = 'USD', r.timestamp = datetime('2026-08-09T10:00:00Z'), r.scenario_id = 'SC_LAYERED_01', r.transaction_type = 'layering', r.channel = 'online';

MATCH (l2b:Account {account_id: 'A017'}), (l3:Account {account_id: 'A007'})
MERGE (l2b)-[r:TRANSFERRED_TO {transaction_id: 'TX_LAY_004'}]->(l3)
ON CREATE SET r.amount = 8800.0, r.currency = 'USD', r.timestamp = datetime('2026-08-09T10:15:00Z'), r.scenario_id = 'SC_LAYERED_01', r.transaction_type = 'layering', r.channel = 'online';

MATCH (l3:Account {account_id: 'A007'}), (l4a:Account {account_id: 'A008'})
MERGE (l3)-[r:TRANSFERRED_TO {transaction_id: 'TX_LAY_005'}]->(l4a)
ON CREATE SET r.amount = 8500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-09T11:00:00Z'), r.scenario_id = 'SC_LAYERED_01', r.transaction_type = 'dispersion', r.channel = 'wire';

MATCH (l3:Account {account_id: 'A007'}), (l4b:Account {account_id: 'A009'})
MERGE (l3)-[r:TRANSFERRED_TO {transaction_id: 'TX_LAY_006'}]->(l4b)
ON CREATE SET r.amount = 8500.0, r.currency = 'USD', r.timestamp = datetime('2026-08-09T11:15:00Z'), r.scenario_id = 'SC_LAYERED_01', r.transaction_type = 'dispersion', r.channel = 'wire';
