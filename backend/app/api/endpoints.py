import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlmodel import Session, select, func, desc
from app.database import get_session
from app.models import Account, Transaction, ImportBatch, ImportSource, Category
from app.parsers.registry import detect_and_parse
from app.services.ingestion_service import ingest_transactions
from app.services.transfer_service import pair_inter_account_transfers
from app.services.firefly_service import load_firefly_reference_data, reconcile_with_firefly
from app.services.ssh_service import list_remote_statement_files, sync_remote_files

router = APIRouter(prefix="/api")

@router.get("/health")
def health_check():
    return {"status": "ok", "app": "FinanceHub"}

@router.get("/accounts")
def list_accounts(session: Session = Depends(get_session)):
    accounts = session.exec(select(Account).order_by(Account.name)).all()
    return accounts

@router.get("/transactions")
def list_transactions(
    session: Session = Depends(get_session),
    account_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0
):
    count_query = select(func.count(Transaction.id))
    query = select(Transaction).order_by(desc(Transaction.date), desc(Transaction.id))
    if account_id:
        query = query.where(Transaction.account_id == account_id)
        count_query = count_query.where(Transaction.account_id == account_id)
    if search:
        s = f"%{search.lower()}%"
        cond = (
            func.lower(Transaction.payee).like(s) |
            func.lower(Transaction.description).like(s)
        )
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = session.exec(count_query).one()
    txs = session.exec(query.offset(offset).limit(limit)).all()

    # Preload account names
    items = []
    for t in txs:
        t_dict = t.model_dump()
        t_dict["account_name"] = t.account.name if t.account else "Unknown"
        t_dict["category_name"] = t.category.name if t.category else None
        items.append(t_dict)

    return {"total": total, "items": items, "offset": offset, "limit": limit}

@router.post("/upload")
async def upload_statement_files(
    files: List[UploadFile] = File(...),
    session: Session = Depends(get_session)
):
    results = []
    for file in files:
        content = await file.read()
        bank_name, norm_txs = detect_and_parse(content, file.filename)
        if norm_txs:
            batch, imported, skipped = ingest_transactions(
                session=session,
                transactions=norm_txs,
                filename=file.filename,
                source=ImportSource.WEB_UPLOAD
            )
            results.append({
                "filename": file.filename,
                "bank": bank_name,
                "imported": imported,
                "skipped": skipped,
                "status": "SUCCESS"
            })
        else:
            results.append({
                "filename": file.filename,
                "bank": bank_name,
                "imported": 0,
                "skipped": 0,
                "status": "UNRECOGNIZED_OR_EMPTY"
            })

    pair_inter_account_transfers(session)
    return {"results": results}

@router.get("/remote/files")
def get_remote_files():
    try:
        files = list_remote_statement_files()
        return [
            {"filename": f.filename, "size": f.size, "modified_time": f.modified_time}
            for f in files
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to remote SSH server: {str(e)}")

@router.post("/sync/ssh")
def trigger_ssh_sync(
    filenames: Optional[List[str]] = None,
    session: Session = Depends(get_session)
):
    try:
        results = sync_remote_files(session=session, filenames=filenames)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH Sync error: {str(e)}")

@router.get("/reconciliation")
def get_reconciliation_report(session: Session = Depends(get_session)):
    dataset = load_firefly_reference_data()
    report = reconcile_with_firefly(session, dataset)
    return {
        "matched_count": report.matched_count,
        "missing_in_statement_count": report.missing_in_statement_count,
        "missing_in_firefly_count": report.missing_in_firefly_count,
        "amount_mismatch_count": report.amount_mismatch_count,
        "account_diffs": report.account_diffs,
        "details": report.details[:200] # return first 200 details
    }

@router.get("/analytics/net-worth")
def get_net_worth_analytics(session: Session = Depends(get_session)):
    accounts = session.exec(select(Account)).all()
    net_worth = sum(a.current_balance for a in accounts)
    assets = sum(a.current_balance for a in accounts if a.current_balance > 0)
    debts = sum(a.current_balance for a in accounts if a.current_balance < 0)

    # Calculate last 6 months cash flow (excluding internal transfers)
    from app.models import TransactionType
    txs = session.exec(
        select(Transaction)
        .where(Transaction.transaction_type != TransactionType.TRANSFER)
        .order_by(Transaction.date)
    ).all()
    monthly: dict = {}
    for t in txs:
        m_key = t.date.strftime("%Y-%m")
        if m_key not in monthly:
            monthly[m_key] = {"month": m_key, "income": 0.0, "expense": 0.0}
        if t.amount > 0:
            monthly[m_key]["income"] += t.amount
        else:
            monthly[m_key]["expense"] += abs(t.amount)

    flow_list = sorted(list(monthly.values()), key=lambda x: x["month"])[-6:]

    return {
        "net_worth": round(net_worth, 2),
        "assets": round(assets, 2),
        "debts": round(debts, 2),
        "cash_flow": flow_list
    }
