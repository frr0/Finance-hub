import io
import pandas as pd
from typing import List
from .base import BaseBankParser, NormalizedTransaction, clean_amount, parse_date_str

class BBVAParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "BBVA"

    def can_parse(self, content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if "bbva" in fn:
            return True
        if "elenco delle transazioni" in fn:
            return True
        # Check CSV header
        if fn.endswith(".csv"):
            header_sample = content[:400].decode("utf-8", errors="ignore")
            if "Parola chiave" in header_sample and "Disponibile" in header_sample:
                return True
        return False

    def parse(self, content: bytes, filename: str) -> List[NormalizedTransaction]:
        transactions: List[NormalizedTransaction] = []
        fn = filename.lower()

        if fn.endswith(".csv"):
            # BBVA CSV has duplicate 'Valuta' column names
            df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")
            # Rename columns positionally or make unique
            cols = []
            seen = {}
            for col in df.columns:
                c = str(col).strip()
                if c in seen:
                    seen[c] += 1
                    cols.append(f"{c}_{seen[c]}")
                else:
                    seen[c] = 0
                    cols.append(c)
            df.columns = cols

            for _, row in df.iterrows():
                dt = parse_date_str(row.get("Data", row.get("Data valuta")))
                amt = clean_amount(row.get("Importo"))
                payee = str(row.get("Parola chiave", "")).strip()
                movimento = str(row.get("Movimento", "")).strip()
                osservazioni = str(row.get("Osservazioni", "")).strip()
                desc = f"{movimento} - {osservazioni}".strip(" -")

                transactions.append(NormalizedTransaction(
                    date=dt,
                    account_name="BBVA",
                    amount=amt,
                    currency="EUR",
                    payee=payee or "BBVA Movimento",
                    description=desc,
                    source_file=filename,
                    raw_payload=row.to_dict()
                ))

        else:
            # Excel export (e.g. Card transactions)
            # Find header row containing 'Data' and 'Importo'
            df_raw = pd.read_excel(io.BytesIO(content), header=None)
            header_idx = None
            for idx, r in df_raw.iterrows():
                row_str = " ".join([str(v) for v in r.values])
                if "Data" in row_str and "Importo" in row_str:
                    header_idx = idx
                    break

            if header_idx is not None:
                df = pd.read_excel(io.BytesIO(content), skiprows=header_idx)
                for _, row in df.iterrows():
                    dt = parse_date_str(row.get("Data"))
                    amt = clean_amount(row.get("Importo"))
                    causale = str(row.get("Causale", "")).strip()
                    carta = str(row.get("Carta", "")).strip()

                    transactions.append(NormalizedTransaction(
                        date=dt,
                        account_name="BBVA",
                        amount=amt,
                        currency="EUR",
                        payee=causale or "BBVA Carta",
                        description=f"Carta: {carta} - {causale}".strip(" -"),
                        source_file=filename,
                        raw_payload=row.to_dict()
                    ))

        return transactions
