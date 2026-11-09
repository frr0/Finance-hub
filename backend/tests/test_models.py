import pytest
from datetime import date, datetime
from sqlmodel import SQLModel, Session, create_engine, select
from app.models import (
    Account, AccountType,
    Transaction, TransactionType,
    Category, PortfolioHolding,
    ImportBatch, ImportSource,
    ReconciliationSnapshot
)

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_account_and_transaction(session: Session):
    account = Account(
        name="BBVA Checking",
        type=AccountType.CHECKING,
        currency="EUR",
        current_balance=1000.0,
        baseline_balance=500.0
    )
    session.add(account)
    session.commit()
    session.refresh(account)

    assert account.id is not None
    assert account.name == "BBVA Checking"
    assert account.type == AccountType.CHECKING

    tx = Transaction(
        account_id=account.id,
        date=date(2026, 3, 24),
        amount=-100.0,
        currency="EUR",
        payee="Directa R6133",
        description="Bonifico eseguito a favore di Directa",
        transaction_type=TransactionType.EXPENSE,
        fingerprint="sha256_mock_fp_123"
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)

    assert tx.id is not None
    assert tx.amount == -100.0
    assert tx.account_id == account.id
    assert tx.transaction_type == TransactionType.EXPENSE

def test_unique_fingerprint_constraint(session: Session):
    account = Account(name="Revolut", type=AccountType.CHECKING, currency="EUR")
    session.add(account)
    session.commit()

    tx1 = Transaction(
        account_id=account.id,
        date=date(2026, 3, 20),
        amount=-9.99,
        currency="EUR",
        payee="Iliad",
        description="Canone mensile",
        transaction_type=TransactionType.EXPENSE,
        fingerprint="unique_fp_1"
    )
    session.add(tx1)
    session.commit()

    tx2 = Transaction(
        account_id=account.id,
        date=date(2026, 3, 20),
        amount=-9.99,
        currency="EUR",
        payee="Iliad",
        description="Canone mensile duplicate",
        transaction_type=TransactionType.EXPENSE,
        fingerprint="unique_fp_1"
    )
    session.add(tx2)
    with pytest.raises(Exception):
        session.commit()
