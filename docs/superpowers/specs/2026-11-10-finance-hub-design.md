# Design Document: FinanceHub — Firefly-Inspired Personal Finance WebApp

**Date:** 2026-11-10  
**Author:** Antigravity  
**Target Repository:** `/home/francesco/Progetti/Webapp/finance-hub`  
**Status:** Approved Specification (Post-Builder Review)

---

## 1. Intent & The Why

### Background
The user relies on Firefly III for tracking personal finances across multiple accounts (ING, BBVA, Revolut, Satispay, Directa, Amex, PayPal, Fondo Fo.nTe., etc.). However, Firefly III's built-in data importer frequently fails on real-world bank exports due to:
- Multi-row metadata preambles before tables (e.g., American Express `movimenti.xlsx`, Directa `P_TOTALE_*.csv`).
- Duplicate column names in exports (e.g., BBVA CSVs containing two `Valuta` columns).
- Complex cell values with emojis and custom statuses (e.g., Satispay `Esporta report.xlsx` featuring `📈 Deposito Investimento`, `🛡️ Deposito Risparmi`).
- Mixed date encodings (Excel floating serial days in Revolut/Satispay, Italian `DD/MM/YYYY`, US `MM/DD/YYYY`).
- Comma-delimited European numbers with currency symbols.

Furthermore, bank statement files accumulate remotely on `server@192.168.1.185` in `~/Scaricati/robe/Scaricati`. Manual downloading, cleaning, and uploading through Firefly's web interface is tedious, error-prone, and frustrating.

### Purpose
To deliver **FinanceHub**, an independent, modern personal finance web application packaged in Docker. It combines the financial clarity and depth inspired by Firefly III with a resilient bank parsing engine and automated SSH synchronization, capable of verifying numbers directly against existing Firefly III records.

---

## 2. Goals, Non-Goals & Anti-Goals

### Goals
1. **Automated SSH Ingestion**: Fetch spreadsheet/statement files (`.csv`, `.xlsx`, `.xls`) on demand from `server@192.168.1.185:~/Scaricati/robe/Scaricati` over SSH/SFTP.
2. **Frictionless Web Upload**: Drag-and-drop web UI to upload single or multiple files directly, with automatic bank detection and interactive preview.
3. **Robust Multi-Bank Parsers**: Custom, fault-tolerant parsers for:
   - **BBVA** (Account CSV & Card XLSX)
   - **Revolut** (Account Statement XLSX with serial date conversion)
   - **Satispay** (Export XLSX with category emoji sanitization and money box logic)
   - **American Express** (PAYBACK XLSX skipping header metadata blocks)
   - **Directa** (Portfolio CSV and Asset XLSX with title row stripping)
   - **PayPal** (Activity CSV handling US dates and comma amounts)
   - **Generic Fallback Parser** (Heuristic date/amount/description detection for other banks like ING)
4. **Firefly III Reconciliation Engine**: Ingest existing Firefly III transactions and account balances from the local database (live connection to `firefly-db` or offline fallback to `/home/francesco/Progetti/Webapp/firefly/init.sql`) and present a side-by-side reconciliation dashboard highlighting discrepancies, missing transactions, and balance deltas per account.
5. **Interactive Dashboard & Ledger**: Modern web UI featuring net worth over time, account balances, categorization, monthly cash flow charts, and a full-text searchable transaction ledger.
6. **One-Command Local Docker Setup**: Standard `docker-compose.yml` exposing the web application on a local port (`30095`), running smoothly with minimal resource consumption.

### Non-Goals
- Multi-user authentication / OAuth login: Designed as a single-user local appliance; simple password or local-only network restriction is sufficient.
- Live PSD2/OpenBanking automated banking sync APIs: Real bank APIs require licensed aggregators (Tink/Nordigen); file-based ingestion from SSH and browser is the explicit goal.
- Complex multi-currency forex trading calculations: Standard multi-currency support (EUR primary) is supported, but advanced forex position hedging is out of scope.

### Anti-Goals
- Never overwrite or modify the existing Firefly III database/installation (`/home/francesco/Progetti/Webapp/firefly` remains read-only for reconciliation).
- Never discard unparsed rows silently: Any unparseable transaction must be flagged in an "Import Exceptions" queue for manual resolution.

---

## 3. Constraints

- **Host Environment**: Linux x86_64, Docker + Docker Compose installed.
- **Remote Host**: `server@192.168.1.185`, key-based SSH already working without interactive password.
- **Firefly Reference**: `/home/francesco/Progetti/Webapp/firefly/init.sql` exists and contains ~10,800 historical transaction rows; running MariaDB container exists in `firefly_net`.
- **Performance**: Capable of parsing and indexing 20,000+ transactions within seconds using SQLite.

---

## 4. Approaches Considered

### Approach 1: Unified FastAPI Service with Server-Rendered UI (Single Container)
- Python FastAPI + SQLite + Jinja2/HTMX + Tailwind.
- *Pros*: Single container, minimal footprint.
- *Cons*: Clunkier UI for deep table filtering, transaction inline-editing, and visual diff trees compared to modern client-side SPAs.

### Approach 2: Python FastAPI Engine Backend + React/Vite Modern Dashboard (Selected)
- Backend: FastAPI (Python 3.12) with Pandas, OpenPyXL, Paramiko (SSH), SQLAlchemy / SQLModel, SQLite.
- Frontend: React 18 + Vite + Tailwind CSS + Lucide Icons + TanStack Table + Recharts.
- Packaged as a unified Docker Compose application (or multi-stage production container with static frontend served by FastAPI/Nginx).
- *Pros*: Best-in-class parsing robustness (Pandas/OpenPyXL) coupled with a fluid, modern, desktop-grade dashboard matching and exceeding Firefly III's UI.
- *Cons*: Requires compiling the React frontend in the Docker build step.

**Decision**: Approach 2 was selected for its superior user experience and clear separation between data parsing and interactive UI.

---

## 5. Architectural & Builder Decisions

Following builder review, the following key engineering calls are codified:

1. **Firefly Integration Strategy (Live DB Peering with Offline Fallback)**:
   - FinanceHub joins `firefly_net` as an external Docker network.
   - When `firefly-db` is accessible, it pulls live accounts and transaction journals using async MySQL read queries.
   - If `firefly-db` is unreachable, it parses `/home/francesco/Progetti/Webapp/firefly/init.sql` directly into memory/cache.
2. **Account Balances & Baseline Calculation**:
   - Accounts track an initial baseline balance (bootstrapped from Firefly's historical balances).
   - Parsers for institutions providing running balances (BBVA `Disponibile`, Revolut `Saldo`) record verified balance checkpoints with timestamps.
   - Calculated ledger balances are verified against latest statement checkpoints, raising visual alert badges if a mismatch occurs.
3. **Internal Transfers & Anti-Double-Counting**:
   - `Transaction` entity includes `transaction_type`: `EXPENSE`, `INCOME`, `TRANSFER`.
   - Ingestion automatically flags and pairs matching internal transfers (e.g., checking account debit to credit card bill, checking debit to Satispay wallet top-up, or bank-to-bank transfers) within a configurable 3-day window.
4. **Directa Holdings vs. Cash Transactions**:
   - `P_TOTALE_*.csv` and `Asset_*.xlsx` are handled by an `InvestmentParser` that tracks position holdings (Ticker, Quantity, Market Price, Valuation) updating Net Worth.
   - Cash dividends, fees, and deposits in Directa are normalized as standard cash transactions.
5. **Reconciliation Features**:
   - Side-by-side reconciliation grid comparing Firefly transactions and FinanceHub parsed records.
   - Difference highlights: Missing in Firefly, Missing in Statements, Amount Discrepancies, Uncategorized differences.
   - Single-click action: "Export Clean CSV for Firefly Data Importer" to easily feed Firefly if desired.
6. **Deterministic Deduplication Rule**:
   - Uses native external transaction UUID when present (e.g., Satispay).
   - For banks without unique IDs: Generates a SHA-256 fingerprint from `(account_id, date, amount, normalized_payee, sequence_in_day)`.
   - Overlapping file imports gracefully detect and ignore existing fingerprints while displaying an import audit summary.

---

## 6. System Architecture

```
                                      +---------------------------------------------+
                                      |   Remote Server (192.168.1.185)             |
                                      |   ~/Scaricati/robe/Scaricati                |
                                      |   (BBVA, Amex, Revolut, Satispay, Directa)  |
                                      +----------------------+----------------------+
                                                             | (SFTP / SSH)
                                                             v
+-----------------------------------------------------------------------------------+
|  FinanceHub Docker Environment                                                    |
|                                                                                   |
|  +--------------------+       REST API       +---------------------------------+  |
|  | React / Vite UI    | <==================> | FastAPI Backend                 |  |
|  | - Accounts Overview|                      | - SSH Sync Worker (Paramiko)    |  |
|  | - Drag & Drop Imprt|                      | - Multi-Bank Pandas Parsers     |  |
|  | - Reconcile Diff   |                      | - Firefly Live/Dump Reader      |  |
|  | - Ledger & Charts  |                      | - Transfer & Dedup Engine       |  |
|  +--------------------+                      +----------------+----------------+  |
|                                                               |                   |
|                                                               v                   |
|                                                      +-----------------+          |
|                                                      | SQLite Database |          |
|                                                      +-----------------+          |
+-----------------------------------------------------------------------------------+
                                                               ^ (Read-Only)
                                                               |
+--------------------------------------------------------------+--------------------+
|  Firefly III Local Reference                                                      |
|  - firefly-db (MariaDB via firefly_net)                                           |
|  - /home/francesco/Progetti/Webapp/firefly/init.sql                               |
+-----------------------------------------------------------------------------------+
```

---

## 7. Data Models

### 7.1 Database Schema (SQLite / SQLAlchemy)
- **Account**: `id`, `name`, `type` (`CHECKING`, `SAVINGS`, `CREDIT_CARD`, `INVESTMENT`, `CASH`), `currency`, `current_balance`, `baseline_balance`, `last_synced_at`.
- **Transaction**: `id`, `account_id`, `destination_account_id` (for transfers), `date`, `amount`, `currency`, `payee`, `description`, `category_id`, `transaction_type` (`EXPENSE`, `INCOME`, `TRANSFER`), `reference_id`, `fingerprint` (unique constraint), `import_batch_id`.
- **Category**: `id`, `name`, `icon`, `color`.
- **PortfolioHolding**: `id`, `account_id`, `symbol`, `name`, `quantity`, `current_price`, `total_value`, `updated_at`.
- **ImportBatch**: `id`, `source` (`SSH_REMOTE`, `WEB_UPLOAD`), `filename`, `imported_at`, `total_rows`, `imported_count`, `skipped_count`, `status`.
- **ReconciliationSnapshot**: `id`, `account_name`, `firefly_balance`, `financehub_balance`, `difference`, `checked_at`.

---

## 8. Deployment & Configuration

- **Directory**: `/home/francesco/Progetti/Webapp/finance-hub`
- **Docker Compose**:
  - `web`: Serves compiled React UI and FastAPI backend (or decoupled frontend/backend services).
  - Port mapping: `30095:8000` (avoids Firefly on `30090` and importer on `30091`).
  - Volumes:
    - `./data:/app/data` (persistent database & upload cache)
    - `/home/francesco/.ssh:/root/.ssh:ro` (read-only SSH credentials for `192.168.1.185`)
    - `/home/francesco/Progetti/Webapp/firefly/init.sql:/app/firefly_reference/init.sql:ro` (Firefly offline dump)
  - Networks:
    - `finance_net` (internal)
    - `firefly_net` (peered to communicate with `firefly-db` if running)
