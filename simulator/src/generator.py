"""
FinGraph Graph-Aware Synthetic Transaction Generator.
Produces deterministic entity populations (Banks, People, Accounts) and emits realistic
normal commercial transactions alongside structured fraud syndicate topologies.
"""
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from faker import Faker
try:
    from simulator.src.models import (
        Account,
        AccountType,
        Bank,
        Currency,
        Person,
        ScenarioID,
        TransactionEvent,
        TransactionType,
    )
except ImportError:
    from models import (
        Account,
        AccountType,
        Bank,
        Currency,
        Person,
        ScenarioID,
        TransactionEvent,
        TransactionType,
    )


class FinGraphGenerator:
    """
    Deterministic Graph-Aware Synthetic Data Generator for AML and Fraud Analytics.
    """

    def __init__(
        self,
        num_accounts: int = 200,
        num_people: int = 150,
        num_banks: int = 10,
        seed: Optional[int] = 42,
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.faker = Faker()
        if seed is not None:
            self.faker.seed_instance(seed)

        self.banks: Dict[str, Bank] = {}
        self.people: Dict[str, Person] = {}
        self.accounts: Dict[str, Account] = {}

        # Categorized accounts for realistic behavioral routing
        self.business_accounts: List[str] = []
        self.retail_accounts: List[str] = []
        self.mule_accounts: List[str] = []
        self.offshore_accounts: List[str] = []

        self._tx_counter = 100000
        self._current_sim_time = datetime.now(timezone.utc) - timedelta(days=3)

        self._initialize_population(num_banks, num_people, num_accounts)

    def _next_tx_id(self) -> str:
        self._tx_counter += 1
        return f"TX{self._tx_counter}"

    def _initialize_population(self, num_banks: int, num_people: int, num_accounts: int) -> None:
        """Create deterministic banks, people, and accounts."""
        # 1. Banks
        bank_names = [
            "Apex Global Bank",
            "Horizon Trust Bank",
            "Pinnacle Credit Union",
            "Sterling Standard Bank",
            "Vanguard Commercial Bank",
            "Pacific Rim Financial",
            "Midwest Commerce Bank",
            "Atlantic Reserve",
            "Alpine Private Bank",
            "Nordic Continental",
        ]
        for i in range(num_banks):
            b_id = f"B{i+1:02d}"
            b_name = bank_names[i] if i < len(bank_names) else f"Bank {self.faker.company()}"
            self.banks[b_id] = Bank(
                bank_id=b_id,
                name=b_name,
                country=self.rng.choice(["US", "GB", "DE", "CA", "CH", "SG"]),
                routing_number=f"0{self.rng.randint(10000000, 99999999)}"
            )

        # 2. People / Corporate Entities
        for i in range(num_people):
            p_id = f"P{i+1:03d}"
            is_corp = self.rng.random() < 0.20
            p_name = self.faker.company() if is_corp else self.faker.name()
            self.people[p_id] = Person(
                person_id=p_id,
                name=p_name,
                email=self.faker.safe_email(),
                country=self.rng.choice(["US", "GB", "DE", "CA", "CH", "SG"]),
                created_at=self._current_sim_time - timedelta(days=self.rng.randint(30, 365))
            )

        # 3. Accounts
        person_ids = list(self.people.keys())
        bank_ids = list(self.banks.keys())

        for i in range(num_accounts):
            a_id = f"A{i+1:03d}"
            owner_id = self.rng.choice(person_ids)
            bank_id = self.rng.choice(bank_ids)

            # Assign account type distribution
            roll = self.rng.random()
            if roll < 0.60:
                acc_type = AccountType.CHECKING
                self.retail_accounts.append(a_id)
            elif roll < 0.80:
                acc_type = AccountType.SAVINGS
                self.retail_accounts.append(a_id)
            elif roll < 0.90:
                acc_type = AccountType.BUSINESS
                self.business_accounts.append(a_id)
            elif roll < 0.95:
                acc_type = AccountType.INTERMEDIARY
                self.mule_accounts.append(a_id)
            elif roll < 0.98:
                acc_type = AccountType.SHELL_BUSINESS
                self.mule_accounts.append(a_id)
            else:
                acc_type = AccountType.OFFSHORE
                self.offshore_accounts.append(a_id)

            self.accounts[a_id] = Account(
                account_id=a_id,
                account_type=acc_type,
                owner_person_id=owner_id,
                bank_id=bank_id,
                risk_score=round(self.rng.uniform(5.0, 20.0), 1),
                created_at=self._current_sim_time - timedelta(days=self.rng.randint(10, 200))
            )

        # Safeguard lists in case of low accounts count
        if not self.business_accounts:
            self.business_accounts = [list(self.accounts.keys())[0]]
        if not self.retail_accounts:
            self.retail_accounts = list(self.accounts.keys())
        if not self.mule_accounts:
            self.mule_accounts = self.retail_accounts[:3]
        if not self.offshore_accounts:
            self.offshore_accounts = self.retail_accounts[-2:]

    def _build_event(
        self,
        from_acc_id: str,
        to_acc_id: str,
        amount: float,
        tx_type: TransactionType,
        scenario_id: str,
        channel: str = "online",
        timestamp_offset_seconds: int = 0
    ) -> TransactionEvent:
        """Helper to create a fully hydrated TransactionEvent."""
        from_acc = self.accounts[from_acc_id]
        to_acc = self.accounts[to_acc_id]
        from_p = self.people[from_acc.owner_person_id]
        to_p = self.people[to_acc.owner_person_id]

        tx_time = self._current_sim_time + timedelta(seconds=timestamp_offset_seconds)

        return TransactionEvent(
            transaction_id=self._next_tx_id(),
            timestamp=tx_time,
            from_account=from_acc_id,
            to_account=to_acc_id,
            amount=round(amount, 2),
            currency=Currency.USD,
            from_person=from_p.name,
            to_person=to_p.name,
            bank=from_acc.bank_id,
            transaction_type=tx_type,
            scenario_id=scenario_id,
            channel=channel,
            status="COMPLETED",
            is_synthetic=True,
            created_at=datetime.now(timezone.utc)
        )

    # --------------------------------------------------------------------------
    # Normal Transaction Generators
    # --------------------------------------------------------------------------

    def generate_normal_salary(self) -> TransactionEvent:
        """Employer business account paying monthly/biweekly salary to employee."""
        employer = self.rng.choice(self.business_accounts)
        employee = self.rng.choice(self.retail_accounts)
        while employee == employer:
            employee = self.rng.choice(self.retail_accounts)

        amount = self.rng.uniform(2500.0, 9500.0)
        return self._build_event(
            from_acc_id=employer,
            to_acc_id=employee,
            amount=amount,
            tx_type=TransactionType.SALARY,
            scenario_id=ScenarioID.SC_NORMAL.value,
            channel="wire"
        )

    def generate_normal_purchase(self) -> TransactionEvent:
        """Consumer checking account paying retail merchant or service."""
        consumer = self.rng.choice(self.retail_accounts)
        merchant = self.rng.choice(self.business_accounts)
        while merchant == consumer:
            merchant = self.rng.choice(self.business_accounts)

        amount = self.rng.uniform(8.50, 450.0)
        return self._build_event(
            from_acc_id=consumer,
            to_acc_id=merchant,
            amount=amount,
            tx_type=TransactionType.PURCHASE,
            scenario_id=ScenarioID.SC_NORMAL.value,
            channel=self.rng.choice(["pos", "online", "mobile"])
        )

    def generate_normal_transfer(self) -> TransactionEvent:
        """Peer-to-peer transfer between known retail accounts."""
        acc1 = self.rng.choice(self.retail_accounts)
        acc2 = self.rng.choice(self.retail_accounts)
        while acc2 == acc1:
            acc2 = self.rng.choice(self.retail_accounts)

        amount = self.rng.uniform(20.0, 750.0)
        return self._build_event(
            from_acc_id=acc1,
            to_acc_id=acc2,
            amount=amount,
            tx_type=TransactionType.TRANSFER,
            scenario_id=ScenarioID.SC_NORMAL.value,
            channel="mobile"
        )

    def generate_normal_bill(self) -> TransactionEvent:
        """Consumer paying recurring utility, mortgage, or credit bill."""
        consumer = self.rng.choice(self.retail_accounts)
        utility = self.rng.choice(self.business_accounts)
        while utility == consumer:
            utility = self.rng.choice(self.business_accounts)

        amount = self.rng.uniform(60.0, 1800.0)
        return self._build_event(
            from_acc_id=consumer,
            to_acc_id=utility,
            amount=amount,
            tx_type=TransactionType.BILL_PAYMENT,
            scenario_id=ScenarioID.SC_NORMAL.value,
            channel="online"
        )

    def generate_normal_event(self) -> TransactionEvent:
        """Emits a random normal commercial/retail transaction."""
        choice = self.rng.choices(
            [self.generate_normal_purchase, self.generate_normal_transfer, self.generate_normal_salary, self.generate_normal_bill],
            weights=[0.50, 0.25, 0.15, 0.10],
            k=1
        )[0]
        return choice()

    # --------------------------------------------------------------------------
    # Suspicious Fraud Syndicate Pattern Generators
    # --------------------------------------------------------------------------

    def generate_funnel_scenario(self, scenario_tag: Optional[str] = None) -> List[TransactionEvent]:
        """
        Pattern A: Funnel / Smurfing.
        Multiple source accounts send structured sub-$10k transfers to an intermediary mule,
        which aggregates and sweeps the total to an offshore/beneficiary account.
        A1, A2, A3, A4 -> I1 -> B1
        """
        tag = scenario_tag or f"{ScenarioID.SC_FUNNEL_01.value}_{uuid.uuid4().hex[:6]}"
        mule = self.rng.choice(self.mule_accounts)
        sources = [acc for acc in self.rng.sample(self.retail_accounts, min(4, len(self.retail_accounts))) if acc != mule]
        destination = self.rng.choice(self.offshore_accounts)
        while destination == mule or destination in sources:
            destination = self.rng.choice(list(self.accounts.keys()))

        events: List[TransactionEvent] = []
        total_aggregated = 0.0
        time_offset = 0

        # Inflow: Structuring under $10,000 threshold ($7,500 - $9,950)
        for src in sources:
            amt = self.rng.uniform(7500.0, 9950.0)
            total_aggregated += amt
            events.append(self._build_event(
                from_acc_id=src,
                to_acc_id=mule,
                amount=amt,
                tx_type=TransactionType.SMURFING,
                scenario_id=tag,
                channel="online",
                timestamp_offset_seconds=time_offset
            ))
            time_offset += self.rng.randint(30, 180)

        # Outflow: Rapid sweep to destination
        fee = total_aggregated * 0.02
        sweep_amt = total_aggregated - fee
        events.append(self._build_event(
            from_acc_id=mule,
            to_acc_id=destination,
            amount=sweep_amt,
            tx_type=TransactionType.PASS_THROUGH,
            scenario_id=tag,
            channel="wire",
            timestamp_offset_seconds=time_offset + 300
        ))

        return events

    def generate_distribution_scenario(self, scenario_tag: Optional[str] = None) -> List[TransactionEvent]:
        """
        Pattern B: One-to-Many Dispersion.
        Single source account rapidly distributes funds into 5 to 10 destination accounts.
        S -> D1, D2, D3, D4, D5
        """
        tag = scenario_tag or f"{ScenarioID.SC_DISTRIB_01.value}_{uuid.uuid4().hex[:6]}"
        source = self.rng.choice(self.business_accounts + self.mule_accounts)
        destinations = [acc for acc in self.rng.sample(self.retail_accounts, min(6, len(self.retail_accounts))) if acc != source]

        events: List[TransactionEvent] = []
        time_offset = 0
        total_disbursed = self.rng.uniform(30000.0, 70000.0)
        slice_amt = total_disbursed / len(destinations)

        for dst in destinations:
            # Vary amount slightly (+- 5%) to avoid trivial identical value detection
            jitter = self.rng.uniform(0.95, 1.05)
            amt = slice_amt * jitter
            events.append(self._build_event(
                from_acc_id=source,
                to_acc_id=dst,
                amount=amt,
                tx_type=TransactionType.DISPERSION,
                scenario_id=tag,
                channel="wire",
                timestamp_offset_seconds=time_offset
            ))
            time_offset += self.rng.randint(20, 90)

        return events

    def generate_chain_scenario(self, scenario_tag: Optional[str] = None) -> List[TransactionEvent]:
        """
        Pattern C: Intermediary Chain (Multi-hop Layering).
        Funds traverse a linear chain of 4-5 accounts to obscure money origin.
        A -> B -> C -> D -> E
        """
        tag = scenario_tag or f"{ScenarioID.SC_CHAIN_01.value}_{uuid.uuid4().hex[:6]}"
        chain_len = self.rng.randint(4, 5)
        chain_nodes = self.rng.sample(list(self.accounts.keys()), chain_len)

        events: List[TransactionEvent] = []
        current_amount = self.rng.uniform(15000.0, 45000.0)
        time_offset = 0

        for i in range(len(chain_nodes) - 1):
            src = chain_nodes[i]
            dst = chain_nodes[i+1]
            events.append(self._build_event(
                from_acc_id=src,
                to_acc_id=dst,
                amount=current_amount,
                tx_type=TransactionType.PASS_THROUGH,
                scenario_id=tag,
                channel="online",
                timestamp_offset_seconds=time_offset
            ))
            # Subtract 1-2% intermediary pass-through cut
            current_amount *= self.rng.uniform(0.98, 0.99)
            time_offset += self.rng.randint(60, 300)

        return events

    def generate_circular_scenario(self, scenario_tag: Optional[str] = None) -> List[TransactionEvent]:
        """
        Pattern D: Circular Flow (Wash Trading Loop).
        Closed cycle returning funds back to origin: A -> B -> C -> A.
        """
        tag = scenario_tag or f"{ScenarioID.SC_CIRCULAR_01.value}_{uuid.uuid4().hex[:6]}"
        cycle_len = self.rng.randint(3, 4)
        cycle_nodes = self.rng.sample(self.mule_accounts + self.business_accounts, min(cycle_len, len(self.mule_accounts + self.business_accounts)))
        if len(cycle_nodes) < 3:
            cycle_nodes = self.rng.sample(list(self.accounts.keys()), 3)

        events: List[TransactionEvent] = []
        start_amount = self.rng.uniform(8500.0, 25000.0)
        current_amount = start_amount
        time_offset = 0

        for i in range(len(cycle_nodes)):
            src = cycle_nodes[i]
            dst = cycle_nodes[(i + 1) % len(cycle_nodes)]
            events.append(self._build_event(
                from_acc_id=src,
                to_acc_id=dst,
                amount=current_amount,
                tx_type=TransactionType.CIRCULAR,
                scenario_id=tag,
                channel="wire",
                timestamp_offset_seconds=time_offset
            ))
            current_amount *= self.rng.uniform(0.985, 0.995)
            time_offset += self.rng.randint(60, 240)

        return events

    def generate_layered_network_scenario(self, scenario_tag: Optional[str] = None) -> List[TransactionEvent]:
        """
        Pattern E: Layered Network (Multi-tier Syndicate).
        Layer 1 (3 Sources) -> Layer 2 (2 Intermediaries) -> Layer 3 (1 Pool) -> Layer 4 (2 Exits)
        """
        tag = scenario_tag or f"{ScenarioID.SC_LAYERED_01.value}_{uuid.uuid4().hex[:6]}"
        all_accs = list(self.accounts.keys())
        selected = self.rng.sample(all_accs, min(8, len(all_accs)))

        l1_sources = selected[0:3]
        l2_intermediates = selected[3:5]
        l3_pool = selected[5]
        l4_exits = selected[6:8]

        events: List[TransactionEvent] = []
        time_offset = 0
        l2_balances = {l2_intermediates[0]: 0.0, l2_intermediates[1]: 0.0}

        # Step 1: L1 -> L2
        for i, src in enumerate(l1_sources):
            target_l2 = l2_intermediates[i % len(l2_intermediates)]
            amt = self.rng.uniform(6000.0, 9500.0)
            l2_balances[target_l2] += amt
            events.append(self._build_event(
                from_acc_id=src,
                to_acc_id=target_l2,
                amount=amt,
                tx_type=TransactionType.LAYERING,
                scenario_id=tag,
                timestamp_offset_seconds=time_offset
            ))
            time_offset += self.rng.randint(30, 90)

        # Step 2: L2 -> L3 Pool
        total_pooled = 0.0
        for l2 in l2_intermediates:
            amt = l2_balances[l2] * 0.98
            total_pooled += amt
            events.append(self._build_event(
                from_acc_id=l2,
                to_acc_id=l3_pool,
                amount=amt,
                tx_type=TransactionType.LAYERING,
                scenario_id=tag,
                timestamp_offset_seconds=time_offset
            ))
            time_offset += self.rng.randint(60, 120)

        # Step 3: L3 Pool -> L4 Exits
        exit_slice = (total_pooled * 0.97) / len(l4_exits)
        for exit_acc in l4_exits:
            events.append(self._build_event(
                from_acc_id=l3_pool,
                to_acc_id=exit_acc,
                amount=exit_slice,
                tx_type=TransactionType.DISPERSION,
                scenario_id=tag,
                timestamp_offset_seconds=time_offset
            ))
            time_offset += self.rng.randint(30, 90)

        return events

    def generate_suspicious_scenario(self) -> List[TransactionEvent]:
        """Emits one of the 5 structured fraud syndicate scenarios at random."""
        generator_funcs = [
            self.generate_funnel_scenario,
            self.generate_distribution_scenario,
            self.generate_chain_scenario,
            self.generate_circular_scenario,
            self.generate_layered_network_scenario,
        ]
        return self.rng.choice(generator_funcs)()

    def generate_event_stream(
        self,
        suspicious_rate: float = 0.20,
        batch_size: int = 1
    ) -> List[TransactionEvent]:
        """
        Generates a continuous mix of normal and suspicious transaction events.
        """
        results: List[TransactionEvent] = []
        while len(results) < batch_size:
            if self.rng.random() < suspicious_rate:
                scenario_events = self.generate_suspicious_scenario()
                results.extend(scenario_events)
            else:
                results.append(self.generate_normal_event())

            # Advance simulated time slightly
            self._current_sim_time += timedelta(seconds=self.rng.randint(1, 5))

        return results[:batch_size] if batch_size > 0 else results
