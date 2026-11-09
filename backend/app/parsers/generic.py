import io
import pandas as pd
from typing import List
from .base import BaseBankParser, NormalizedTransaction, clean_amount, parse_date_str

class GenericBankParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "Generic"

    def can_parse(self, content: bytes, filename: str) -> bool:
        return filename.lower().endswith((".csv", ".xlsx", ".xls"))

    def parse(self, content: bytes, filename: str) -> List[NormalizedTransaction]:
        transactions: List[NormalizedTransaction] = []
        fn = filename.lower()

        try:
            if fn.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")
            else:
                df = pd.read_excel(io.BytesIO(content))

            # Detect date column
            date_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["data", "date", "giorno"])), None)
            amount_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["importo", "amount", "totale", "saldo"])), None)
            desc_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["descrizione", "causale", "dettagli", "beneficiario", "note"])), None)

            if date_col and amount_col:
                for _, row in df.iterrows():
                    dt = parse_date_str(row.get(date_col))
                    amt = clean_amount(row.get(amount_col))
                    desc = str(row.get(desc_col, "Transazione")).strip() if desc_col else "Transazione"

                    transactions.append(NormalizedTransaction(
                        date=dt,
                        account_name="Generic Account",
                        amount=amt,
                        currency="EUR",
                        payee=desc,
                        description=desc,
                        source_file=filename,
                        raw_payload=row.to_dict()
                    ))
        except Exception:
            pass

        return transactions
