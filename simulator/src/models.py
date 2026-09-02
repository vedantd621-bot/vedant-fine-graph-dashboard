"""
FinGraph Data Models (Pydantic V2).
Defines schemas for Transaction Events, People, Accounts, Banks, and Scenario Enums.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    JPY = "JPY"


class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    SHELL_BUSINESS = "shell_business"
    OFFSHORE = "offshore"
    INTERMEDIARY = "intermediary"


class TransactionType(str, Enum):
    SALARY = "salary"
    PURCHASE = "purchase"
    TRANSFER = "transfer"
    BILL_PAYMENT = "bill_payment"
    SMURFING = "smurfing"
    DISPERSION = "dispersion"
    PASS_THROUGH = "pass_through"
    CIRCULAR = "circular"
    LAYERING = "layering"


class ScenarioID(str, Enum):
    SC_NORMAL = "SC_NORMAL"
    SC_FUNNEL_01 = "SC_FUNNEL_01"
    SC_DISTRIB_01 = "SC_DISTRIB_01"
    SC_CHAIN_01 = "SC_CHAIN_01"
    SC_CIRCULAR_01 = "SC_CIRCULAR_01"
    SC_LAYERED_01 = "SC_LAYERED_01"


class Bank(BaseModel):
    """Represents a financial institution hosting accounts."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    bank_id: str = Field(..., min_length=1, description="Unique Bank identifier e.g. B01")
    name: str = Field(..., min_length=1, description="Bank institution name")
    country: str = Field(default="US", min_length=2, max_length=3)
    routing_number: Optional[str] = Field(default=None)


class Person(BaseModel):
    """Represents a human or business entity owning one or more accounts."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    person_id: str = Field(..., min_length=1, description="Unique Person identifier e.g. P101")
    name: str = Field(..., min_length=1, description="Full name or company name")
    email: Optional[str] = Field(default=None)
    country: str = Field(default="US", min_length=2, max_length=3)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Entity registration timestamp (UTC)"
    )


class Account(BaseModel):
    """Represents a bank account node in the transaction graph."""
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(..., min_length=1, description="Unique Account identifier e.g. A101")
    account_type: AccountType = Field(default=AccountType.CHECKING)
    owner_person_id: str = Field(..., min_length=1, description="Foreign key to Person")
    bank_id: str = Field(..., min_length=1, description="Foreign key to Bank")
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0, description="0-100 calculated risk score")
    community_id: Optional[int] = Field(default=None, description="Louvain community syndicate ID")
    pagerank: float = Field(default=0.0, ge=0.0, description="PageRank centrality score")
    is_frozen: bool = Field(default=False, description="Simulated freeze status")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Account creation timestamp (UTC)"
    )


class TransactionEvent(BaseModel):
    """
    Standard JSON Event Contract for financial transactions moving across Kafka, Flink, and Neo4j.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    transaction_id: str = Field(..., min_length=1, description="Globally unique transaction identifier e.g. TX10001")
    timestamp: datetime = Field(..., description="Timezone-aware transaction timestamp (UTC)")
    from_account: str = Field(..., min_length=1, description="Origin Account ID")
    to_account: str = Field(..., min_length=1, description="Destination Account ID")
    amount: float = Field(..., gt=0.0, description="Monetary transfer value, must be positive numeric")
    currency: Currency = Field(default=Currency.USD, description="ISO 4217 Currency Code")
    from_person: str = Field(..., min_length=1, description="Sender Person ID or Name")
    to_person: str = Field(..., min_length=1, description="Receiver Person ID or Name")
    bank: str = Field(..., min_length=1, description="Originating Bank ID")
    transaction_type: TransactionType = Field(default=TransactionType.TRANSFER)
    scenario_id: str = Field(default=ScenarioID.SC_NORMAL.value, description="Scenario traceability tag")
    channel: str = Field(default="online", description="Channel: online | wire | atm | pos | mobile")
    status: str = Field(default="COMPLETED", description="Transaction state")
    is_synthetic: bool = Field(default=True, description="Strict synthetic data flag")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Simulator emission timestamp (UTC)"
    )

    @field_validator("timestamp", mode="after")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def check_non_empty_parties(self) -> "TransactionEvent":
        if not self.from_account.strip():
            raise ValueError("from_account cannot be empty or whitespace")
        if not self.to_account.strip():
            raise ValueError("to_account cannot be empty or whitespace")
        if not self.from_person.strip():
            raise ValueError("from_person cannot be empty or whitespace")
        if not self.to_person.strip():
            raise ValueError("to_person cannot be empty or whitespace")
        if not self.bank.strip():
            raise ValueError("bank cannot be empty or whitespace")
        return self
