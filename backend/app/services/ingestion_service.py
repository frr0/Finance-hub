import hashlib
import datetime
from typing import List, Tuple, Dict
from sqlmodel import Session, select
from app.models import Account, AccountType, Transaction, TransactionType, ImportBatch, ImportSource, Category
from app.parsers.base import NormalizedTransaction

def compute_fingerprint(account_id: int, dt: datetime.date, amount: float, payee: str, seq: int) -> str:
    raw_str = f"{account_id}|{dt.isoformat()}|{amount:.2f}|{payee.strip().lower()}|{seq}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

def get_or_create_account(session: Session, name: str) -> Account:
    account = session.exec(select(Account).where(Account.name == name)).first()
    if not account:
        # Determine likely account type from name
        nl = name.lower()
        if "credit" in nl or "amex" in nl or "american express" in nl:
            acc_type = AccountType.CREDIT_CARD
        elif "savings" in nl or "risparmi" in nl:
            acc_type = AccountType.SAVINGS
        elif "directa" in nl or "invest" in nl or "trade" in nl or "scalable" in nl or "fondo" in nl:
            acc_type = AccountType.INVESTMENT
        elif "cash" in nl or "wallet" in nl:
            acc_type = AccountType.CASH
        else:
            acc_type = AccountType.CHECKING

        account = Account(
            name=name,
            type=acc_type,
            currency="EUR",
            current_balance=0.0,
            baseline_balance=0.0
        )
        session.add(account)
        session.commit()
        session.refresh(account)
    return account

def get_or_create_category(session: Session, name: str) -> Category:
    cat = session.exec(select(Category).where(Category.name == name)).first()
    if not cat:
        cat = Category(name=name)
        session.add(cat)
        session.commit()
        session.refresh(cat)
    return cat

def ingest_transactions(
    session: Session,
    transactions: List[NormalizedTransaction],
    filename: str,
    source: ImportSource = ImportSource.WEB_UPLOAD
) -> Tuple[ImportBatch, int, int]:
    batch = ImportBatch(
        source=source,
        filename=filename,
        total_rows=len(transactions),
        imported_count=0,
        skipped_count=0,
        status="IN_PROGRESS"
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)

    # Track sequence of identical (account, date, amount, payee) inside this batch
    seq_tracker: Dict[Tuple[int, datetime.date, float, str], int] = {}
    imported_cnt = 0
    skipped_cnt = 0

    for norm_tx in transactions:
        account = get_or_create_account(session, norm_tx.account_name)

        key = (account.id, norm_tx.date, norm_tx.amount, norm_tx.payee.strip().lower())
        seq = seq_tracker.get(key, 0) + 1
        seq_tracker[key] = seq

        fp = compute_fingerprint(account.id, norm_tx.date, norm_tx.amount, norm_tx.payee, seq)

        # Check existing fingerprint in database
        existing = session.exec(select(Transaction).where(Transaction.fingerprint == fp)).first()
        if existing:
            skipped_cnt += 1
            continue

        cat_id = None
        if norm_tx.category:
            cat = get_or_create_category(session, norm_tx.category)
            cat_id = cat.id

        tx_type = TransactionType.INCOME if norm_tx.amount > 0 else TransactionType.EXPENSE

        db_tx = Transaction(
            account_id=account.id,
            date=norm_tx.date,
            amount=norm_tx.amount,
            currency=norm_tx.currency,
            payee=norm_tx.payee,
            description=norm_tx.description,
            category_id=cat_id,
            transaction_type=tx_type,
            reference_id=norm_tx.reference_id,
            fingerprint=fp,
            source_file=filename,
            import_batch_id=batch.id
        )
        session.add(db_tx)

        # Update account balance and last synced
        if norm_tx.category == "Portfolio Valuation":
            account.current_balance = norm_tx.amount
        else:
            account.current_balance += norm_tx.amount
        account.last_synced_at = datetime.datetime.now(datetime.timezone.utc)
        session.add(account)

        imported_cnt += 1

    batch.imported_count = imported_cnt
    batch.skipped_count = skipped_cnt
    batch.status = "COMPLETED"
    session.add(batch)
    session.commit()
    session.refresh(batch)

    return batch, imported_cnt, skipped_cnt
