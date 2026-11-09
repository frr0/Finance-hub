import datetime
import pytest
from sqlmodel import SQLModel, Session, create_engine
from app.models import Account, AccountType, Transaction, TransactionType
from app.services.firefly_service import (
    parse_firefly_sql_dump,
    reconcile_with_firefly,
    FireflyDataset,
    ReconciliationReport
)

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_parse_firefly_sql_dump():
    sample_sql = """
    INSERT INTO `accounts` VALUES
    (1,'2026-08-02 18:38:51','2026-10-28 09:22:44',NULL,1,1,1,'ING',0.000000000000,NULL,1,0,0,NULL),
    (5,'2026-08-02 19:07:00','2026-10-28 09:22:47',NULL,1,1,1,'Revolut',NULL,NULL,1,0,3,NULL),
    (6,'2026-08-02 19:07:11','2026-08-02 20:00:24',NULL,1,1,1,'BBVA',NULL,NULL,1,0,5,NULL);

    INSERT INTO `transaction_journals` VALUES
    (1,'2026-08-02 19:12:23','2026-08-02 19:12:38',NULL,1,1,7,1,NULL,1,'satispay','2026-08-02 19:11:00','Europe/Rome',NULL,NULL,NULL,0,0,1,1),
    (5,'2026-08-02 19:46:10','2026-08-02 20:00:24',NULL,1,1,7,5,NULL,1,'Trenitalia - pt wl','2026-08-02 00:00:00','Europe/Rome',NULL,NULL,NULL,0,0,1,1);

    INSERT INTO `transactions` VALUES
    (1,'2026-08-02 19:12:23','2026-08-02 19:12:38',NULL,0,1,1,NULL,1,-10.500000000000,0.0,-10.5,0,NULL,NULL,0,NULL,NULL),
    (2,'2026-08-02 19:46:10','2026-08-02 20:00:24',NULL,0,6,5,NULL,1,-3.300000000000,0.0,-3.3,0,NULL,NULL,0,NULL,NULL);
    """

    dataset = parse_firefly_sql_dump(sample_sql)
    assert len(dataset.accounts) == 3
    assert dataset.accounts[6]["name"] == "BBVA"
    assert len(dataset.transactions) == 2
    assert dataset.transactions[0]["amount"] == -10.5
    assert dataset.transactions[1]["description"] == "Trenitalia - pt wl"
    assert dataset.transactions[1]["amount"] == -3.3

def test_reconcile_with_firefly(session: Session):
    # Setup local account and transaction
    bbva = Account(name="BBVA", type=AccountType.CHECKING, currency="EUR", current_balance=-3.3)
    session.add(bbva)
    session.commit()

    tx = Transaction(
        account_id=bbva.id,
        date=datetime.date(2026, 8, 2),
        amount=-3.3,
        currency="EUR",
        payee="Trenitalia",
        description="Trenitalia ticket",
        transaction_type=TransactionType.EXPENSE,
        fingerprint="fp_trenitalia_1"
    )
    session.add(tx)
    session.commit()

    dataset = FireflyDataset(
        accounts={
            1: {"id": 1, "name": "BBVA", "balance": -3.3}
        },
        transactions=[
            {
                "id": 1,
                "account_name": "BBVA",
                "date": datetime.date(2026, 8, 2),
                "amount": -3.3,
                "description": "Trenitalia"
            },
            {
                "id": 2,
                "account_name": "BBVA",
                "date": datetime.date(2026, 8, 3),
                "amount": -20.0,
                "description": "Missing In FinanceHub"
            }
        ]
    )

    report = reconcile_with_firefly(session, dataset)
    assert report.matched_count == 1
    assert report.missing_in_statement_count == 1
    assert len(report.account_diffs) >= 1
