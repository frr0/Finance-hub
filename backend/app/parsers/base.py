import re
import datetime
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class NormalizedTransaction:
    date: datetime.date
    account_name: str
    amount: float
    currency: str = "EUR"
    payee: str = ""
    description: str = ""
    category: Optional[str] = None
    reference_id: Optional[str] = None
    source_file: str = ""
    raw_payload: Dict[str, Any] = field(default_factory=dict)

def clean_amount(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    s = s.replace("€", "").replace("EUR", "").replace("eur", "").strip()
    # Check European format: 1.234,56 or -1.234,56 or 9657,57
    if "," in s and "." in s:
        # If dot comes before comma, dot is thousand separator
        if s.find(".") < s.find(","):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    s = re.sub(r"[^\d.-]", "", s)
    if not s or s == "-":
        return 0.0
    return float(s)

def parse_date_str(val: Any) -> datetime.date:
    if val is None:
        return datetime.date.today()
    if isinstance(val, datetime.date):
        return val
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, (int, float)):
        # Excel floating serial date: day 1 is 1899-12-30 in Excel
        try:
            return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(val))).date()
        except Exception:
            return datetime.date.today()
    s = str(val).strip()
    # Try common formats
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    # If date string has time part (e.g. 2026/03/29 17:34:33)
    try:
        return datetime.datetime.fromisoformat(s.replace("/", "-")).date()
    except Exception:
        pass
    return datetime.date.today()

class BaseBankParser(ABC):
    @property
    @abstractmethod
    def bank_name(self) -> str:
        pass

    @abstractmethod
    def can_parse(self, content: bytes, filename: str) -> bool:
        pass

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> List[NormalizedTransaction]:
        pass
