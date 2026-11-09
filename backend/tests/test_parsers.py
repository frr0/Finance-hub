import io
import datetime
import pytest
import pandas as pd
from app.parsers.bbva import BBVAParser
from app.parsers.amex import AmexParser
from app.parsers.satispay import SatispayParser
from app.parsers.revolut import RevolutParser
from app.parsers.directa import DirectaParser
from app.parsers.paypal import PayPalParser
from app.parsers.registry import detect_and_parse

def test_bbva_csv_parser():
    # BBVA CSV has duplicate 'Valuta' column names and comma decimal numbers
    csv_content = (
        "Data valuta,Data,Parola chiave,Movimento,Importo,Valuta,Disponibile,Valuta,Osservazioni\n"
        "24/03/2026,24/03/2026,Bonifico eseguito,Codice cliente n. r6133,-100,EUR,\"9657,57\",EUR,codice cliente n. R6133\n"
        "18/03/2026,20/03/2026,Trenitalia - pt wl,Pagamento con carta,\"-3,3\",EUR,\"11762,57\",EUR,5179090000975628 TRENITALIA\n"
    ).encode("utf-8")

    parser = BBVAParser()
    assert parser.can_parse(csv_content, "Patrimonio - BBVA.csv")
    txs = parser.parse(csv_content, "Patrimonio - BBVA.csv")
    assert len(txs) == 2
    assert txs[0].amount == -100.0
    assert txs[0].date == datetime.date(2026, 3, 24)
    assert txs[0].account_name == "BBVA"
    assert txs[1].amount == -3.3
    assert txs[1].date == datetime.date(2026, 3, 20)
    assert "Trenitalia" in txs[1].payee

def test_bbva_card_xlsx_parser():
    # BBVA Card XLSX has title metadata rows before table header at row 5
    df_rows = [
        ["", "", "", "", ""],
        ["", "Elenco delle transazioni", "", "", ""],
        ["", "Data di generazione del rapporto: 29/03/2026", "", "", ""],
        ["", "", "", "", ""],
        ["Data", "Carta", "Causale", "Importo", "Valuta"],
        ["18/03/2026", "5179090000975628", "Trenitalia - pt wl", "-3.3", "€"]
    ]
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        pd.DataFrame(df_rows).to_excel(writer, index=False, header=False)
    content = bio.getvalue()

    parser = BBVAParser()
    assert parser.can_parse(content, "2026Y-03M-29D-15_13_34-Elenco delle transazioni.xlsx")
    txs = parser.parse(content, "2026Y-03M-29D-15_13_34-Elenco delle transazioni.xlsx")
    assert len(txs) == 1
    assert txs[0].amount == -3.3
    assert txs[0].date == datetime.date(2026, 3, 18)
    assert "Trenitalia" in txs[0].payee

def test_amex_xlsx_parser():
    # Amex XLSX has cardholder preamble rows
    df_rows = [
        ["Dettagli transazione", "Carta di Credito PAYBACK American Express® / 12 Mar, 2026 a 11 Apr, 2026"],
        ["Per", ""],
        ["FRANCESCO RANELLUCCI", ""],
        ["Numero di Carta", ""],
        ["XXXX-XXXXXX-01005", ""],
        ["", ""],
        ["Data", "Descrizione", "Importo"],
        ["15/03/2026", "ESSELUNGA TORINO", "-54.20"],
        ["20/03/2026", "AMAZON.IT", "-19.99"]
    ]
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        pd.DataFrame(df_rows).to_excel(writer, index=False, header=False)
    content = bio.getvalue()

    parser = AmexParser()
    assert parser.can_parse(content, "movimenti.xlsx")
    txs = parser.parse(content, "movimenti.xlsx")
    assert len(txs) == 2
    assert txs[0].amount == -54.20
    assert txs[0].date == datetime.date(2026, 3, 15)
    assert txs[0].account_name == "American Express"
    assert txs[1].amount == -19.99

def test_satispay_xlsx_parser():
    # Satispay has emoji categories and Excel floating timestamps
    # Excel date 46106 is approx 2026-03-25
    df = pd.DataFrame([
        {
            "Data": 46106.6409,
            "Nome": "Salvadanaio Investito",
            "Descrizione": "",
            "Importo": "-0.7",
            "Tipo": "📈 Deposito Investimento",
            "Stato": "✅ Approvato",
            "Disponibilità": "-0.7",
            "Disponibilità dopo la transazione": "98.5",
            "ID (Comunicalo all'Assistenza Clienti in caso di problemi)": "019d2560-8b9e-7267-9767-812205fdc839"
        },
        {
            "Data": 46106.6317,
            "Nome": "Dubai Coffee Lounge",
            "Descrizione": "Caffe e cornetto",
            "Importo": "-1.3",
            "Tipo": "🏬 a un Negozio",
            "Stato": "✅ Approvato",
            "Disponibilità": "-1.3",
            "Disponibilità dopo la transazione": "99.2",
            "ID (Comunicalo all'Assistenza Clienti in caso di problemi)": "019d2554-7ee2-72f9-8a7f-5198cfcdc875"
        }
    ])
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    content = bio.getvalue()

    parser = SatispayParser()
    assert parser.can_parse(content, "Esporta report.xlsx")
    txs = parser.parse(content, "Esporta report.xlsx")
    assert len(txs) == 2
    assert txs[1].amount == -1.3
    assert txs[1].account_name == "Satispay"
    assert txs[1].reference_id == "019d2554-7ee2-72f9-8a7f-5198cfcdc875"
    assert "Coffee Lounge" in txs[1].payee

def test_revolut_xlsx_parser():
    df = pd.DataFrame([
        {
            "Tipo": "Pagamento con carta",
            "Prodotto": "Attuale",
            "Data di inizio": 46105.43,
            "Data di completamento": 46106.18,
            "Descrizione": "iliad",
            "Importo": "-9.99",
            "Costo": "0.0",
            "Valuta": "EUR",
            "State": "COMPLETATO",
            "Saldo": "90.01"
        }
    ])
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    content = bio.getvalue()

    parser = RevolutParser()
    assert parser.can_parse(content, "account-statement_2026.xlsx")
    txs = parser.parse(content, "account-statement_2026.xlsx")
    assert len(txs) == 1
    assert txs[0].amount == -9.99
    assert txs[0].account_name == "Revolut"
    assert txs[0].payee == "iliad"

def test_paypal_csv_parser():
    csv_content = (
        "Data,Descrizione,Importo\n"
        "03/27/2026,PAYPAL *TRENITALIAS     892021,\"3,30\"\n"
        "03/22/2026,PAYPAL *VERY MOBILE     4029357733,\"5,99\"\n"
    ).encode("utf-8")

    parser = PayPalParser()
    assert parser.can_parse(csv_content, "activity.csv")
    txs = parser.parse(csv_content, "activity.csv")
    assert len(txs) == 2
    assert txs[0].amount == -3.30 # expenses normalized to negative
    assert txs[0].date == datetime.date(2026, 3, 27)
    assert txs[0].account_name == "PayPal"

def test_registry_dispatcher():
    csv_content = (
        "Data valuta,Data,Parola chiave,Movimento,Importo,Valuta,Disponibile,Valuta,Osservazioni\n"
        "24/03/2026,24/03/2026,Bonifico eseguito,Directa,-100,EUR,\"9657,57\",EUR,R6133\n"
    ).encode("utf-8")
    bank_name, txs = detect_and_parse(csv_content, "Patrimonio - BBVA.csv")
    assert bank_name == "BBVA"
    assert len(txs) == 1
