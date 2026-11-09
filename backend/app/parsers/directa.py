import io
import re
import datetime
import pandas as pd
from typing import List
from .base import BaseBankParser, NormalizedTransaction, clean_amount, parse_date_str

class DirectaParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "Directa"

    def can_parse(self, content: bytes, filename: str) -> bool:
        fn = filename.lower()
        if "directa" in fn or "p_totale" in fn or "asset_" in fn:
            return True
        return False

    def parse(self, content: bytes, filename: str) -> List[NormalizedTransaction]:
        transactions: List[NormalizedTransaction] = []
        fn = filename.lower()

        if fn.endswith(".csv"):
            text = content.decode("utf-8", errors="ignore")
            # Extract date if available
            date_match = re.search(r"Data estrazione\s*:\s*(\d{4}/\d{2}/\d{2})", text)
            dt = parse_date_str(date_match.group(1)) if date_match else datetime.date.today()

            # Extract portfolio total value
            val_match = re.search(r"Valore portafoglio\s*:\s*([\d,.]+)\s*€?", text)
            if val_match:
                total_val = clean_amount(val_match.group(1))
                transactions.append(NormalizedTransaction(
                    date=dt,
                    account_name="Directa",
                    amount=total_val,
                    currency="EUR",
                    payee="Directa Portafoglio",
                    description=f"Valore totale portafoglio: {total_val} EUR",
                    category="Portfolio Valuation",
                    source_file=filename,
                    raw_payload={"valore_portafoglio": total_val}
                ))
        else:
            # Excel asset file
            try:
                df = pd.read_excel(io.BytesIO(content))
                # If there are cash transactions / movements
                for _, row in df.iterrows():
                    row_str = " ".join([str(v) for v in row.values])
                    if "totale" in row_str.lower():
                        continue
                    # Check for date and amount columns
                    dt = parse_date_str(row.get("Data", datetime.date.today()))
                    amt = clean_amount(row.get("Importo", row.get("Controvalore", 0.0)))
                    desc = str(row.get("Descrizione", row.get("Titolo", "Directa Asset"))).strip()
                    if amt != 0.0:
                        transactions.append(NormalizedTransaction(
                            date=dt,
                            account_name="Directa",
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
