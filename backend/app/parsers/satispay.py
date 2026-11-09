import io
import re
import pandas as pd
from typing import List
from .base import BaseBankParser, NormalizedTransaction, clean_amount, parse_date_str

class SatispayParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "Satispay"

    def can_parse(self, content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if "satispay" in fn:
            return True
        if "esporta report" in fn or "esporta_report" in fn:
            return True
        return False

    def parse(self, content: bytes, filename: str) -> List[NormalizedTransaction]:
        transactions: List[NormalizedTransaction] = []
        df = pd.read_excel(io.BytesIO(content))

        for _, row in df.iterrows():
            dt_val = row.get("Data")
            if pd.isna(dt_val):
                continue
            dt = parse_date_str(dt_val)
            amt = clean_amount(row.get("Importo"))
            payee = str(row.get("Nome", "")).strip()
            desc = str(row.get("Descrizione", "")).strip() if not pd.isna(row.get("Descrizione")) else ""
            raw_type = str(row.get("Tipo", "")).strip()
            clean_category = re.sub(r"[^\w\s]", "", raw_type).strip() # clean emojis
            ref_id = str(row.get("ID (Comunicalo all'Assistenza Clienti in caso di problemi)", "")).strip()

            transactions.append(NormalizedTransaction(
                date=dt,
                account_name="Satispay",
                amount=amt,
                currency="EUR",
                payee=payee or "Satispay Payment",
                description=desc or raw_type,
                category=clean_category or None,
                reference_id=ref_id or None,
                source_file=filename,
                raw_payload=row.to_dict()
            ))

        return transactions
