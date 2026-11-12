# FinanceHub 💰

A high-performance, containerized personal finance manager inspired by **Firefly III**, built for friction-free statement ingestion and verification.

## Highlights
- **Resilient Multi-Bank Parsers**: Handles tricky formats that break Firefly III's standard importer:
  - **BBVA**: Duplicate `Valuta` columns, comma decimals, and card export header preambles.
  - **American Express (PAYBACK)**: Dynamic skipping of multi-line cardholder header blocks.
  - **Satispay**: Handles emojis (`📈 Deposito Investimento`, `🛡️ Deposito Risparmi`), money box transfers, and UUID deduplication.
  - **Revolut**: Serial numeric dates and completed transaction filtering.
  - **Directa**: Portfolio valuation and asset movements.
  - **PayPal**: US date format standardizing with European comma amounts.
- **SSH Remote Ingestion**: Discovers and pulls statement files from `server@192.168.1.185:~/Scaricati/robe/Scaricati`.
- **Firefly III Reconciliation**: Compares balances and transactions against your Firefly III database (`init.sql`) to verify zero data loss and spotlight differences.
- **Modern Responsive Dashboard**: React + Vite + Tailwind UI with Net Worth tracking, interactive ledger, and cash flow charts.
- **Anti-Double-Counting**: Automatic pairing of internal transfers (e.g., BBVA to Amex card bill, Satispay wallet top-ups).

## Quick Start (Docker)

```bash
cd /home/francesco/Progetti/Bank-app
docker compose up -d --build
```

Access the web interface at **[http://localhost:30095](http://localhost:30095)**.

## Local Development (Without Docker)

### Backend
```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Run test suite:
```bash
PYTHONPATH=backend pytest backend/tests/
```
