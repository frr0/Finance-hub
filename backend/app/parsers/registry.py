from typing import Tuple, List, Optional
from .base import NormalizedTransaction, BaseBankParser
from .bbva import BBVAParser
from .amex import AmexParser
from .satispay import SatispayParser
from .revolut import RevolutParser
from .directa import DirectaParser
from .paypal import PayPalParser
from .generic import GenericBankParser

ALL_PARSERS: List[BaseBankParser] = [
    BBVAParser(),
    AmexParser(),
    SatispayParser(),
    RevolutParser(),
    DirectaParser(),
    PayPalParser(),
    GenericBankParser(),
]

def detect_and_parse(content: bytes, filename: str) -> Tuple[str, List[NormalizedTransaction]]:
    for parser in ALL_PARSERS:
        if parser.can_parse(content, filename):
            try:
                txs = parser.parse(content, filename)
                if txs or not isinstance(parser, GenericBankParser):
                    return parser.bank_name, txs
            except Exception as e:
                # If specialized parser fails, continue to next/fallback
                continue
    return "Unknown", []
