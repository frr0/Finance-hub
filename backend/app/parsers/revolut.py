import io
import pandas as pd
from typing import List
from .base import BaseBankParser, NormalizedTransaction, clean_amount, parse_date_str

class RevolutParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "Revolut"

    def can_parse(self, content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if "revolut" in fn:
            return True
        if fn.startswith("account-statement") and fn.endswith(".xlsx"):
            return True
        return False

    def parse(self, content: bytes, filename: str) -> List[NormalizedTransaction]:
        transactions: List[NormalizedTransaction] = []
        df = pd.read_excel(io.BytesIO(content))

        for _, row in df.iterrows():
            state = str(row.get("State", "")).strip().upper()
            if state and state not in ("COMPLETATO", "COMPLETED"):
                continue

            dt_val = row.get("Data di completamento", row.get("Data di inizio"))
            if pd.isna(dt_val):
                continue
            dt = parse_date_str(dt_val)
            amt = clean_amount(row.get("Importo"))
            desc = str(row.get("Descrizione", "")).strip()
            tipo = str(row.get("Tipo", "")).strip()

            transactions.append(NormalizedTransaction(
                date=dt,
                account_name="Revolut",
                amount=amt,
                currency="EUR",
                payee=desc or "Revolut Transaction",
                description=f"{tipo}: {desc}".strip(" :"),
                category=tipo or None,
                source_file=filename,
                raw_payload=row.to_dict()
            ))

        return transactions
