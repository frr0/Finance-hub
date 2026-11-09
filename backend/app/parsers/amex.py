import io
import pandas as pd
from typing import List
from .base import BaseBankParser, NormalizedTransaction, clean_amount, parse_date_str

class AmexParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "American Express"

    def can_parse(self, content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if "amex" in fn or "american express" in fn:
            return True
        if fn.startswith("movimenti") and fn.endswith(".xlsx"):
            try:
                df_head = pd.read_excel(io.BytesIO(content), nrows=10, header=None)
                full_text = " ".join(str(val) for row in df_head.values for val in row).lower()
                if "american express" in full_text or "payback" in full_text or "dettagli transazione" in full_text:
                    return True
            except Exception:
                pass
        return False

    def parse(self, content: bytes, filename: str) -> List[NormalizedTransaction]:
        transactions: List[NormalizedTransaction] = []
        df_raw = pd.read_excel(io.BytesIO(content), header=None)

        header_idx = None
        for idx, r in df_raw.iterrows():
            row_vals = [str(v).lower() for v in r.values]
            if "data" in row_vals and ("importo" in row_vals or "descrizione" in row_vals):
                header_idx = idx
                break

        if header_idx is not None:
            df = pd.read_excel(io.BytesIO(content), skiprows=header_idx)
            for _, row in df.iterrows():
                dt_val = row.get("Data", row.get("data"))
                if pd.isna(dt_val):
                    continue
                dt = parse_date_str(dt_val)
                amt = clean_amount(row.get("Importo", row.get("importo")))
                desc = str(row.get("Descrizione", row.get("descrizione", ""))).strip()

                transactions.append(NormalizedTransaction(
                    date=dt,
                    account_name="American Express",
                    amount=amt,
                    currency="EUR",
                    payee=desc,
                    description=desc,
                    source_file=filename,
                    raw_payload=row.to_dict()
                ))

        return transactions
