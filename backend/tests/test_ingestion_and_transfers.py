import datetime
import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from app.models import Account, AccountType, Transaction, TransactionType, ImportSource
from app.parsers.base import NormalizedTransaction
from app.services.ingestion_service import ingest_transactions
from app.services.transfer_service import pair_inter_account_transfers

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_ingest_transactions_and_deduplication(session: Session):
    txs = [
        NormalizedTransaction(
            date=datetime.date(2026, 3, 20),
            account_name="BBVA",
            amount=-50.0,
            currency="EUR",
            payee="Supermarket",
            description="Groceries",
            source_file="test.csv"
        ),
        NormalizedTransaction(
            date=datetime.date(2026, 3, 21),
            account_name="BBVA",
            amount=-20.0,
            currency="EUR",
            payee="Coffee Shop",
            description="Coffee",
            source_file="test.csv"
        )
    ]

    # First ingestion
    batch, imported_cnt, skipped_cnt = ingest_transactions(
        session=session,
        transactions=txs,
        filename="test.csv",
        source=ImportSource.WEB_UPLOAD
    )
    assert imported_cnt == 2
    assert skipped_cnt == 0
    assert batch.imported_count == 2

    # Second ingestion of the same transactions (e.g. overlapping month export)
    batch2, imported_cnt2, skipped_cnt2 = ingest_transactions(
        session=session,
        transactions=txs,
        filename="test.csv",
        source=ImportSource.WEB_UPLOAD
    )
    assert imported_cnt2 == 0
    assert skipped_cnt2 == 2

    # Verify total transactions in database is still 2
    all_txs = session.exec(select(Transaction)).all()
    assert len(all_txs) == 2

def test_pair_inter_account_transfers(session: Session):
    # Setup two accounts: BBVA and Revolut
    bbva = Account(name="BBVA", type=AccountType.CHECKING, currency="EUR")
    revolut = Account(name="Revolut", type=AccountType.CHECKING, currency="EUR")
    session.add(bbva)
    session.add(revolut)
    session.commit()

    # Outflow on BBVA on 2026-03-10: -100 EUR to Revolut
    tx_out = [
        NormalizedTransaction(
            date=datetime.date(2026, 3, 10),
            account_name="BBVA",
            amount=-100.0,
            currency="EUR",
            payee="Revolut Top-up",
            description="Bonifico istantaneo Revolut",
            source_file="bbva.csv"
        )
    ]
    # Inflow on Revolut on 2026-03-11: +100 EUR
    tx_in = [
        NormalizedTransaction(
            date=datetime.date(2026, 3, 11),
            account_name="Revolut",
            amount=100.0,
            currency="EUR",
            payee="Top-up from BBVA",
            description="Ricarica carta",
            source_file="revolut.xlsx"
        )
    ]

    ingest_transactions(session, tx_out, "bbva.csv", ImportSource.WEB_UPLOAD)
    ingest_transactions(session, tx_in, "revolut.xlsx", ImportSource.WEB_UPLOAD)

    # Check transactions before pairing
    txs_before = session.exec(select(Transaction)).all()
    assert all(t.transaction_type != TransactionType.TRANSFER for t in txs_before)

    # Run pairing
    paired_count = pair_inter_account_transfers(session, window_days=3)
    assert paired_count == 1

    # Verify transactions are marked as TRANSFER and linked
    txs_after = session.exec(select(Transaction)).all()
    assert all(t.transaction_type == TransactionType.TRANSFER for t in txs_after)
    debit = next(t for t in txs_after if t.amount < 0)
    credit = next(t for t in txs_after if t.amount > 0)
    assert debit.destination_account_id == credit.account_id
    assert credit.destination_account_id == debit.account_id
