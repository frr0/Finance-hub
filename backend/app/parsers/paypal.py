import io
import pandas as pd
from typing import List
from .base import BaseBankParser, NormalizedTransaction, clean_amount, parse_date_str

class PayPalParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "PayPal"

    def can_parse(self, content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if "paypal" in fn or fn == "activity.csv":
            return True
        if fn.endswith(".csv"):
            sample = content[:200].decode("utf-8", errors="ignore")
            if "Data,Descrizione,Importo" in sample:
                return True
        return False

    def parse(self, content: bytes, filename: str) -> List[NormalizedTransaction]:
        transactions: List[NormalizedTransaction] = []
        df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")

        for _, row in df.iterrows():
            dt_val = row.get("Data")
            if pd.isna(dt_val):
                continue
            dt = parse_date_str(dt_val)
            amt = clean_amount(row.get("Importo"))
            desc = str(row.get("Descrizione", "")).strip()

            # PayPal activity.csv often records purchases as positive numbers
            # If description is a merchant charge and amount > 0, negate it
            if amt > 0 and ("PAYPAL *" in desc or "PAGAMENTO" in desc.upper()):
                amt = -amt

            transactions.append(NormalizedTransaction(
                date=dt,
                account_name="PayPal",
                amount=amt,
                currency="EUR",
                payee=desc or "PayPal Payment",
                description=desc,
                source_file=filename,
                raw_payload=row.to_dict()
            ))

        return transactions
