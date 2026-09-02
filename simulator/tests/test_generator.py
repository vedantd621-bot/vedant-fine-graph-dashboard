"""
Unit tests for FinGraph Generator and Fraud Pattern Topologies.
"""
import pytest
from simulator.src.generator import FinGraphGenerator
from simulator.src.models import ScenarioID, TransactionEvent, TransactionType


@pytest.fixture
def generator() -> FinGraphGenerator:
    """Provides a deterministic generator instance for testing."""
    return FinGraphGenerator(
        num_accounts=50,
        num_people=40,
        num_banks=5,
        seed=12345,
    )


def test_generator_population_initialization(generator: FinGraphGenerator):
    """Verify entities are generated deterministically and populated."""
    assert len(generator.banks) == 5
    assert len(generator.people) == 40
    assert len(generator.accounts) == 50
    assert len(generator.retail_accounts) > 0
    assert len(generator.business_accounts) > 0


def test_unique_transaction_ids(generator: FinGraphGenerator):
    """Verify all sequential transaction events have strictly unique IDs."""
    tx_ids = set()
    for _ in range(100):
        ev = generator.generate_normal_event()
        assert ev.transaction_id not in tx_ids
        tx_ids.add(ev.transaction_id)
        assert ev.amount > 0
        assert isinstance(ev, TransactionEvent)


def test_normal_transaction_types(generator: FinGraphGenerator):
    """Verify salary, purchase, transfer, and bill normal transactions."""
    salary = generator.generate_normal_salary()
    assert salary.transaction_type == TransactionType.SALARY
    assert salary.scenario_id == ScenarioID.SC_NORMAL.value
    assert 2500.0 <= salary.amount <= 9500.0

    purchase = generator.generate_normal_purchase()
    assert purchase.transaction_type == TransactionType.PURCHASE
    assert purchase.scenario_id == ScenarioID.SC_NORMAL.value
    assert 8.50 <= purchase.amount <= 450.0

    transfer = generator.generate_normal_transfer()
    assert transfer.transaction_type == TransactionType.TRANSFER
    assert transfer.scenario_id == ScenarioID.SC_NORMAL.value

    bill = generator.generate_normal_bill()
    assert bill.transaction_type == TransactionType.BILL_PAYMENT
    assert bill.scenario_id == ScenarioID.SC_NORMAL.value


def test_pattern_a_funnel_smurfing(generator: FinGraphGenerator):
    """
    Pattern A: Funnel / Smurfing.
    Verify multiple sources -> intermediary -> exit account structure.
    """
    events = generator.generate_funnel_scenario("TEST_FUNNEL_01")
    assert len(events) >= 4  # At least 3 inflows + 1 sweep outflow
    
    # Verify inflows
    inflows = [e for e in events if e.transaction_type == TransactionType.SMURFING]
    outflows = [e for e in events if e.transaction_type == TransactionType.PASS_THROUGH]
    
    assert len(inflows) >= 3
    assert len(outflows) == 1

    mule_acc = outflows[0].from_account
    for inf in inflows:
        assert inf.to_account == mule_acc
        assert 7500.0 <= inf.amount <= 9950.0  # Structuring under $10k
        assert inf.scenario_id == "TEST_FUNNEL_01"

    # Verify sweep amount is approximately sum of inflows minus fee
    total_in = sum(e.amount for e in inflows)
    assert outflows[0].amount < total_in
    assert outflows[0].amount >= total_in * 0.95


def test_pattern_b_distribution(generator: FinGraphGenerator):
    """
    Pattern B: One-to-Many Distribution.
    Verify single source -> multiple destination accounts.
    """
    events = generator.generate_distribution_scenario("TEST_DISTRIB_01")
    assert len(events) >= 5

    source_acc = events[0].from_account
    destinations = set()
    for ev in events:
        assert ev.from_account == source_acc
        assert ev.transaction_type == TransactionType.DISPERSION
        assert ev.scenario_id == "TEST_DISTRIB_01"
        destinations.add(ev.to_account)

    assert len(destinations) == len(events)


def test_pattern_c_intermediary_chain(generator: FinGraphGenerator):
    """
    Pattern C: Intermediary Chain.
    Verify linear path A -> B -> C -> D -> E with minor fee decay.
    """
    events = generator.generate_chain_scenario("TEST_CHAIN_01")
    assert len(events) >= 3

    for i in range(len(events) - 1):
        assert events[i].to_account == events[i+1].from_account
        assert events[i].transaction_type == TransactionType.PASS_THROUGH
        assert events[i].scenario_id == "TEST_CHAIN_01"
        # Each subsequent hop amount is slightly less due to fee
        assert events[i].amount > events[i+1].amount


def test_pattern_d_circular_flow(generator: FinGraphGenerator):
    """
    Pattern D: Circular Flow (Wash Trading).
    Verify closed loop: A -> B -> C -> A.
    """
    events = generator.generate_circular_scenario("TEST_CIRCULAR_01")
    assert len(events) >= 3

    for i in range(len(events)):
        next_i = (i + 1) % len(events)
        assert events[i].to_account == events[next_i].from_account
        assert events[i].transaction_type == TransactionType.CIRCULAR
        assert events[i].scenario_id == "TEST_CIRCULAR_01"


def test_pattern_e_layered_network(generator: FinGraphGenerator):
    """
    Pattern E: Layered Network.
    Verify multi-tier aggregation and disbursement.
    """
    events = generator.generate_layered_network_scenario("TEST_LAYERED_01")
    assert len(events) >= 7
    for ev in events:
        assert ev.scenario_id == "TEST_LAYERED_01"
        assert ev.amount > 0


def test_event_stream_suspicious_ratio(generator: FinGraphGenerator):
    """Verify continuous event stream mixing normal and suspicious scenarios."""
    events = generator.generate_event_stream(suspicious_rate=0.40, batch_size=50)
    assert len(events) == 50
    
    normal_count = sum(1 for e in events if e.scenario_id == ScenarioID.SC_NORMAL.value)
    suspicious_count = len(events) - normal_count

    assert normal_count > 0
    assert suspicious_count > 0
