import datetime
from sqlmodel import Session, select
from app.models import Transaction, TransactionType

TRANSFER_KEYWORDS = [
    "bonifico", "giroconto", "ricarica", "top-up", "topup", "transfer",
    "addebito", "prelievo", "accredito", "carta", "paypal", "satispay",
    "revolut", "bbva", "amex", "american express", "directa", "scalable"
]

def is_likely_transfer(t1: Transaction, t2: Transaction) -> bool:
    text1 = f"{t1.payee} {t1.description}".lower()
    text2 = f"{t2.payee} {t2.description}".lower()
    return any(k in text1 or k in text2 for k in TRANSFER_KEYWORDS)

def pair_inter_account_transfers(session: Session, window_days: int = 3) -> int:
    """
    Scans unpaired transactions to find matching outflow and inflow
    across different accounts within the specified day window,
    verified by transfer keywords or account references.
    """
    debits = session.exec(
        select(Transaction).where(
            Transaction.amount < 0,
            Transaction.transaction_type != TransactionType.TRANSFER
        ).order_by(Transaction.date)
    ).all()

    paired_count = 0

    for debit in debits:
        target_amount = abs(debit.amount)
        min_date = debit.date - datetime.timedelta(days=window_days)
        max_date = debit.date + datetime.timedelta(days=window_days)

        candidates = session.exec(
            select(Transaction).where(
                Transaction.amount == target_amount,
                Transaction.account_id != debit.account_id,
                Transaction.transaction_type != TransactionType.TRANSFER,
                Transaction.date >= min_date,
                Transaction.date <= max_date
            )
        ).all()

        for credit in candidates:
            if is_likely_transfer(debit, credit):
                debit.transaction_type = TransactionType.TRANSFER
                debit.destination_account_id = credit.account_id

                credit.transaction_type = TransactionType.TRANSFER
                credit.destination_account_id = debit.account_id

                session.add(debit)
                session.add(credit)
                session.commit()
                paired_count += 1
                break

    return paired_count
