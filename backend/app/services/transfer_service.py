import datetime
from sqlmodel import Session, select
from app.models import Transaction, TransactionType

def pair_inter_account_transfers(session: Session, window_days: int = 3) -> int:
    """
    Scans unpaired transactions to find matching outflow and inflow
    across different accounts within the specified day window.
    """
    # Find candidate debits (amount < 0, not yet marked as TRANSFER)
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

        # Look for matching credit on a different account
        credit = session.exec(
            select(Transaction).where(
                Transaction.amount == target_amount,
                Transaction.account_id != debit.account_id,
                Transaction.transaction_type != TransactionType.TRANSFER,
                Transaction.date >= min_date,
                Transaction.date <= max_date
            )
        ).first()

        if credit:
            debit.transaction_type = TransactionType.TRANSFER
            debit.destination_account_id = credit.account_id

            credit.transaction_type = TransactionType.TRANSFER
            credit.destination_account_id = debit.account_id

            session.add(debit)
            session.add(credit)
            session.commit()
            paired_count += 1

    return paired_count
