import re
import os
import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from sqlmodel import Session, select
from app.models import Account, Transaction
from app.parsers.base import clean_amount, parse_date_str

@dataclass
class FireflyDataset:
    accounts: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    transactions: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ReconciliationReport:
    matched_count: int
    missing_in_statement_count: int
    missing_in_firefly_count: int
    amount_mismatch_count: int
    account_diffs: List[Dict[str, Any]]
    details: List[Dict[str, Any]]

def parse_sql_values(sql_insert_str: str) -> List[List[str]]:
    """
    Extracts row tuples from INSERT INTO table VALUES (...), (...);
    Handles strings with commas and escaped quotes.
    """
    rows = []
    # Match everything between ( and )
    pattern = re.compile(r"\((.*?)\)(?:,|;)", re.DOTALL)
    for match in pattern.finditer(sql_insert_str):
        row_raw = match.group(1).strip()
        # Parse comma-separated fields respecting quotes
        fields = []
        in_quote = False
        quote_char = ""
        current = []
        i = 0
        while i < len(row_raw):
            c = row_raw[i]
            if c in ("'", '"') and (i == 0 or row_raw[i-1] != "\\"):
                if not in_quote:
                    in_quote = True
                    quote_char = c
                elif quote_char == c:
                    in_quote = False
                    quote_char = ""
                else:
                    current.append(c)
            elif c == "," and not in_quote:
                fields.append("".join(current).strip().strip("'\""))
                current = []
            else:
                current.append(c)
            i += 1
        if current:
            fields.append("".join(current).strip().strip("'\""))
        rows.append(fields)
    return rows

def parse_firefly_sql_dump(sql_text: str) -> FireflyDataset:
    dataset = FireflyDataset()

    # 1. Parse accounts
    acc_match = re.search(r"INSERT INTO `accounts` VALUES\s*(.*?);", sql_text, re.DOTALL)
    if acc_match:
        rows = parse_sql_values(acc_match.group(1) + ";")
        for r in rows:
            if len(r) >= 8:
                try:
                    acc_id = int(r[0])
                    name = r[7]
                    balance = clean_amount(r[8]) if len(r) > 8 and r[8] != "NULL" else 0.0
                    dataset.accounts[acc_id] = {
                        "id": acc_id,
                        "name": name,
                        "balance": balance
                    }
                except Exception:
                    pass

    # 2. Parse transaction_journals
    journals: Dict[int, Dict[str, Any]] = {}
    tj_match = re.search(r"INSERT INTO `transaction_journals` VALUES\s*(.*?);", sql_text, re.DOTALL)
    if tj_match:
        rows = parse_sql_values(tj_match.group(1) + ";")
        for r in rows:
            if len(r) >= 12:
                try:
                    j_id = int(r[0])
                    desc = r[10]
                    dt = parse_date_str(r[11])
                    journals[j_id] = {
                        "id": j_id,
                        "description": desc,
                        "date": dt
                    }
                except Exception:
                    pass

    # 3. Parse transactions
    tx_match = re.search(r"INSERT INTO `transactions` VALUES\s*(.*?);", sql_text, re.DOTALL)
    if tx_match:
        rows = parse_sql_values(tx_match.group(1) + ";")
        for r in rows:
            if len(r) >= 10:
                try:
                    # Col 5 is account_id, Col 6 is transaction_journal_id, Col 9 is amount
                    acc_id = int(r[5])
                    journal_id = int(r[6])
                    amount = clean_amount(r[9])

                    if journal_id in journals:
                        j_info = journals[journal_id]
                        acc_name = dataset.accounts.get(acc_id, {}).get("name", "Unknown Account")
                        dataset.transactions.append({
                            "id": int(r[0]),
                            "journal_id": journal_id,
                            "account_id": acc_id,
                            "account_name": acc_name,
                            "date": j_info["date"],
                            "amount": amount,
                            "description": j_info["description"]
                        })
                except Exception:
                    pass

    return dataset

def load_firefly_reference_data(file_path: Optional[str] = None) -> FireflyDataset:
    path = file_path or os.getenv("FIREFLY_SQL_PATH", "/home/francesco/Progetti/Webapp/firefly/init.sql")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return parse_firefly_sql_dump(f.read())
    return FireflyDataset()

def reconcile_with_firefly(session: Session, dataset: FireflyDataset) -> ReconciliationReport:
    local_accounts = session.exec(select(Account)).all()
    local_txs = session.exec(select(Transaction)).all()

    account_diffs = []
    # Map accounts by name lowercase
    firefly_acc_by_name = {a["name"].strip().lower(): a for a in dataset.accounts.values()}

    for l_acc in local_accounts:
        lname = l_acc.name.strip().lower()
        ff_acc = firefly_acc_by_name.get(lname)
        ff_bal = ff_acc["balance"] if ff_acc else 0.0
        diff = l_acc.current_balance - ff_bal
        account_diffs.append({
            "account_name": l_acc.name,
            "financehub_balance": round(l_acc.current_balance, 2),
            "firefly_balance": round(ff_bal, 2),
            "difference": round(diff, 2)
        })

    # Compare transactions
    details = []
    matched_count = 0
    missing_in_statement_count = 0
    missing_in_firefly_count = 0
    amount_mismatch_count = 0

    # Build index of local transactions by (date, amount)
    local_index: Dict[Tuple[datetime.date, float], List[Transaction]] = {}
    for tx in local_txs:
        key = (tx.date, round(tx.amount, 2))
        local_index.setdefault(key, []).append(tx)

    matched_local_ids = set()

    for ff_tx in dataset.transactions:
        ff_date = ff_tx["date"]
        ff_amt = round(ff_tx["amount"], 2)
        key = (ff_date, ff_amt)

        matched_tx = None
        if key in local_index and local_index[key]:
            matched_tx = local_index[key].pop(0)
            matched_local_ids.add(matched_tx.id)
            matched_count += 1
            details.append({
                "status": "MATCHED",
                "date": ff_date.isoformat(),
                "account": ff_tx["account_name"],
                "amount": ff_amt,
                "description": ff_tx["description"]
            })
        else:
            missing_in_statement_count += 1
            details.append({
                "status": "MISSING_IN_STATEMENT",
                "date": ff_date.isoformat(),
                "account": ff_tx["account_name"],
                "amount": ff_amt,
                "description": ff_tx["description"]
            })

    # Remaining local transactions are missing in firefly
    for tx in local_txs:
        if tx.id not in matched_local_ids:
            missing_in_firefly_count += 1
            details.append({
                "status": "MISSING_IN_FIREFLY",
                "date": tx.date.isoformat(),
                "account": tx.account.name if tx.account else "Account",
                "amount": tx.amount,
                "description": tx.payee or tx.description
            })

    return ReconciliationReport(
        matched_count=matched_count,
        missing_in_statement_count=missing_in_statement_count,
        missing_in_firefly_count=missing_in_firefly_count,
        amount_mismatch_count=amount_mismatch_count,
        account_diffs=account_diffs,
        details=details
    )
