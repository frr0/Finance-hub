from enum import Enum
from typing import Optional, List
import datetime
from sqlmodel import SQLModel, Field, Relationship

class AccountType(str, Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CREDIT_CARD = "CREDIT_CARD"
    INVESTMENT = "INVESTMENT"
    CASH = "CASH"

class TransactionType(str, Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"

class ImportSource(str, Enum):
    SSH_REMOTE = "SSH_REMOTE"
    WEB_UPLOAD = "WEB_UPLOAD"

class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: AccountType = Field(default=AccountType.CHECKING)
    currency: str = Field(default="EUR")
    current_balance: float = Field(default=0.0)
    baseline_balance: float = Field(default=0.0)
    last_synced_at: Optional[datetime.datetime] = Field(default=None)

    transactions: List["Transaction"] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"foreign_keys": "Transaction.account_id"}
    )

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    icon: Optional[str] = Field(default="Tag")
    color: Optional[str] = Field(default="#6366f1")

    transactions: List["Transaction"] = Relationship(back_populates="category")

class ImportBatch(SQLModel, table=True):
    __tablename__ = "import_batches"

    id: Optional[int] = Field(default=None, primary_key=True)
    source: ImportSource = Field(default=ImportSource.WEB_UPLOAD)
    filename: str
    imported_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    total_rows: int = Field(default=0)
    imported_count: int = Field(default=0)
    skipped_count: int = Field(default=0)
    status: str = Field(default="COMPLETED")

    transactions: List["Transaction"] = Relationship(back_populates="import_batch")

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    destination_account_id: Optional[int] = Field(default=None, foreign_key="accounts.id", index=True)
    date: datetime.date = Field(index=True)
    amount: float = Field(index=True)
    currency: str = Field(default="EUR")
    payee: str = Field(index=True)
    description: str = Field(default="")
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    transaction_type: TransactionType = Field(default=TransactionType.EXPENSE)
    reference_id: Optional[str] = Field(default=None, index=True)
    fingerprint: str = Field(unique=True, index=True)
    source_file: Optional[str] = Field(default=None)
    import_batch_id: Optional[int] = Field(default=None, foreign_key="import_batches.id")

    account: Optional[Account] = Relationship(
        back_populates="transactions",
        sa_relationship_kwargs={"foreign_keys": "Transaction.account_id"}
    )
    category: Optional[Category] = Relationship(back_populates="transactions")
    import_batch: Optional[ImportBatch] = Relationship(back_populates="transactions")

class PortfolioHolding(SQLModel, table=True):
    __tablename__ = "portfolio_holdings"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    symbol: str = Field(index=True)
    name: str = Field(default="")
    quantity: float = Field(default=0.0)
    current_price: float = Field(default=0.0)
    total_value: float = Field(default=0.0)
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

class ReconciliationSnapshot(SQLModel, table=True):
    __tablename__ = "reconciliation_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_name: str = Field(index=True)
    firefly_balance: float = Field(default=0.0)
    financehub_balance: float = Field(default=0.0)
    difference: float = Field(default=0.0)
    checked_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
