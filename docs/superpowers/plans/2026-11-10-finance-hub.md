# FinanceHub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and containerize FinanceHub, a local Docker webapp inspired by Firefly III, featuring automated SSH ingestion from `server@192.168.1.185`, fault-tolerant Italian bank statement parsing, and a side-by-side Firefly III reconciliation engine.

**Architecture:** A Python 3.12 FastAPI backend utilizing Pandas/OpenPyXL for parser engines, Paramiko for SSH sync, and SQLModel/SQLite for persistent storage, combined with a modern React/Vite/Tailwind CSS dashboard for drag-and-drop uploads, interactive ledgers, and visual reconciliation diffs, packaged via Docker Compose on port 30095.

**Tech Stack:** Python 3.12, FastAPI, Pandas, OpenPyXL, Paramiko, SQLModel, SQLite, React 18, Vite, Tailwind CSS, Lucide Icons, Docker, Docker Compose.

**Spec:** [docs/superpowers/specs/2026-11-10-finance-hub-design.md](file:///home/francesco/Progetti/Webapp/finance-hub/docs/superpowers/specs/2026-11-10-finance-hub-design.md)

---

## Global Constraints

- Root project directory is `/home/francesco/Progetti/Webapp/finance-hub`.
- Web service binds locally on port `30095` to avoid conflict with Firefly (`30090`) and Data Importer (`30091`).
- Existing Firefly III installation at `/home/francesco/Progetti/Webapp/firefly` is strictly read-only.
- Remote server target: `server@192.168.1.185:~/Scaricati/robe/Scaricati`.
- Docker containers run under `docker-compose.yml` with persistent storage at `./data`.

---

## Review Focus

1. **BBVA CSV duplicate column names:** Two `Valuta` columns in `Patrimonio - BBVA.csv` must not crash Pandas or drop amounts.
2. **American Express multi-row header block:** 5 metadata preamble rows before table header in `movimenti.xlsx` must be dynamically skipped.
3. **Satispay emojis and money box rows:** Transaction types with emojis (`📈 Deposito Investimento`) and UUIDs must parse cleanly without string corruption.
4. **Revolut serial date numbers:** Floats representing dates (`46089.52...`) must accurately convert to valid ISO UTC dates.
5. **Overlapping statement re-imports:** Ingesting the same file twice or overlapping month files must skip existing fingerprints without duplicates or crashes.

---

### Task 1: Backend Scaffolding, Models & Database Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/models.py`
- Create: `backend/app/database.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Produces: `Account`, `Transaction`, `Category`, `PortfolioHolding`, `ImportBatch`, `ReconciliationSnapshot` SQLModel classes.
- Produces: `get_session()`, `init_db(engine)` in `database.py`.

- [ ] **Step 1: Write requirements.txt and failing tests for data models**
  Define requirements (`fastapi`, `uvicorn`, `sqlmodel`, `pandas`, `openpyxl`, `paramiko`, `pytest`, `python-multipart`).
  Write `backend/tests/test_models.py` testing database creation and model CRUD for `Account` and `Transaction`.

- [ ] **Step 2: Run test to verify it fails**
  Run: `pytest backend/tests/test_models.py`
  Expected: FAIL with ModuleNotFoundError / missing models.

- [ ] **Step 3: Implement models.py and database.py**
  Implement SQLModel classes with fields specified in Design Doc Section 7.1. Set up SQLite engine with foreign key support.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest backend/tests/test_models.py`
  Expected: PASS.

- [ ] **Step 5: Commit**
  Run: `git add backend/` && `git commit -m "feat(backend): add data models and database setup"`

---

### Task 2: Multi-Bank Statement Parsers & Registry

**Files:**
- Create: `backend/app/parsers/base.py`
- Create: `backend/app/parsers/bbva.py`
- Create: `backend/app/parsers/revolut.py`
- Create: `backend/app/parsers/satispay.py`
- Create: `backend/app/parsers/amex.py`
- Create: `backend/app/parsers/directa.py`
- Create: `backend/app/parsers/paypal.py`
- Create: `backend/app/parsers/generic.py`
- Create: `backend/app/parsers/registry.py`
- Test: `backend/tests/test_parsers.py`

**Interfaces:**
- Produces: `NormalizedTransaction` dataclass.
- Produces: `BaseBankParser` abstract class with `can_parse()` and `parse()`.
- Produces: `detect_and_parse(file_bytes: bytes, filename: str) -> Tuple[str, List[NormalizedTransaction]]`.

- [ ] **Step 1: Write comprehensive unit tests with real file samples**
  Create `backend/tests/test_parsers.py` with test fixtures modeling the exact headers discovered during recon:
  - BBVA CSV (duplicate `Valuta`, comma decimals)
  - Amex XLSX (5 metadata preamble rows)
  - Satispay XLSX (emojis, UUIDs, money boxes)
  - Revolut XLSX (serial dates, Italian status)
  - Directa CSV (portfolio metadata header)
  - PayPal CSV (MM/DD/YYYY dates with comma amounts)

- [ ] **Step 2: Run test to verify it fails**
  Run: `pytest backend/tests/test_parsers.py`
  Expected: FAIL with "parser not defined".

- [ ] **Step 3: Implement parsers and parser registry**
  Implement each parser using Pandas/OpenPyXL with robust type coercion, emoji handling, and date normalization. Implement `registry.py` auto-detection logic.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest backend/tests/test_parsers.py`
  Expected: PASS all parser tests.

- [ ] **Step 5: Commit**
  Run: `git add backend/app/parsers backend/tests/test_parsers.py` && `git commit -m "feat(parsers): implement resilient multi-bank statement parsers"`

---

### Task 3: Ingestion Pipeline, Deduplication & Inter-Account Transfers

**Files:**
- Create: `backend/app/services/ingestion_service.py`
- Create: `backend/app/services/transfer_service.py`
- Test: `backend/tests/test_ingestion_and_transfers.py`

**Interfaces:**
- Consumes: `NormalizedTransaction` from Task 2.
- Produces: `ingest_transactions(session, transactions, batch_id) -> ImportSummary`.
- Produces: `pair_inter_account_transfers(session, window_days=3) -> int`.

- [ ] **Step 1: Write tests for deduplication and transfer pairing**
  Write tests in `backend/tests/test_ingestion_and_transfers.py`:
  - Verify re-importing identical transactions produces `skipped_count > 0` and zero duplicate rows.
  - Verify a €100 debit from BBVA to Satispay matches a €100 credit on Satispay within 3 days and converts both to `TRANSFER`.

- [ ] **Step 2: Run test to verify it fails**
  Run: `pytest backend/tests/test_ingestion_and_transfers.py`
  Expected: FAIL.

- [ ] **Step 3: Implement ingestion service & transfer pairing**
  Compute deterministic SHA-256 fingerprints. Implement transfer pairing query joining opposite-signed transactions within window.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest backend/tests/test_ingestion_and_transfers.py`
  Expected: PASS.

- [ ] **Step 5: Commit**
  Run: `git commit -m "feat(services): add ingestion deduplication and transfer pairing"`

---

### Task 4: Firefly III Reconciliation Engine

**Files:**
- Create: `backend/app/services/firefly_service.py`
- Test: `backend/tests/test_firefly_reconciliation.py`

**Interfaces:**
- Consumes: `/home/francesco/Progetti/Webapp/firefly/init.sql` or `firefly-db` connection.
- Produces: `load_firefly_data(source_path_or_url) -> FireflyDataset`.
- Produces: `generate_reconciliation_report(session, firefly_data) -> ReconciliationReport`.

- [ ] **Step 1: Write tests for Firefly reconciliation**
  Test loading sample account balances and transaction journals from SQL dump format. Test reconciliation matching logic (`MATCHED`, `MISSING_IN_FIREFLY`, `AMOUNT_MISMATCH`).

- [ ] **Step 2: Run test to verify it fails**
  Run: `pytest backend/tests/test_firefly_reconciliation.py`
  Expected: FAIL.

- [ ] **Step 3: Implement firefly_service.py**
  Implement regex/streaming parser for `init.sql` dumps to extract `accounts`, `transactions`, and `transaction_journals`. Implement fuzzy matching algorithm against FinanceHub SQLite database.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest backend/tests/test_firefly_reconciliation.py`
  Expected: PASS.

- [ ] **Step 5: Commit**
  Run: `git commit -m "feat(services): implement Firefly III reconciliation engine"`

---

### Task 5: SSH Remote File Sync Worker

**Files:**
- Create: `backend/app/services/ssh_service.py`
- Test: `backend/tests/test_ssh_service.py`

**Interfaces:**
- Produces: `list_remote_statement_files(host, user, remote_path) -> List[RemoteFileInfo]`.
- Produces: `fetch_remote_file_content(host, user, remote_path, filename) -> bytes`.

- [ ] **Step 1: Write unit tests with mocked Paramiko SFTP client**
  Test remote directory listing, filtering for spreadsheet extensions (`.csv`, `.xlsx`, `.xls`), and downloading file bytes.

- [ ] **Step 2: Run test to verify it fails**
  Run: `pytest backend/tests/test_ssh_service.py`
  Expected: FAIL.

- [ ] **Step 3: Implement ssh_service.py**
  Use Paramiko with key-based authentication (`~/.ssh/id_rsa`, `id_ed25519` or SSH agent fallback). Add timeout and error handling.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest backend/tests/test_ssh_service.py`
  Expected: PASS.

- [ ] **Step 5: Commit**
  Run: `git commit -m "feat(services): add SSH remote statement sync service"`

---

### Task 6: FastAPI REST API Endpoints & Application Core

**Files:**
- Create: `backend/app/api/endpoints.py`
- Create: `backend/app/main.py`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Exposes:
  - `GET /api/accounts`: List accounts with current balance and trend.
  - `GET /api/transactions`: Paginated, filterable transaction list.
  - `POST /api/upload`: Multi-file upload with auto-parse and import summary.
  - `POST /api/sync/ssh`: Triggers SSH fetch from remote server.
  - `GET /api/reconciliation`: Returns side-by-side Firefly vs FinanceHub reconciliation diff.
  - `GET /api/analytics/net-worth`: Net worth and monthly cash flow data.

- [ ] **Step 1: Write integration tests using FastAPI TestClient**
  Test account creation, file upload endpoint with sample CSV, and reconciliation endpoint.

- [ ] **Step 2: Run test to verify it fails**
  Run: `pytest backend/tests/test_api.py`
  Expected: FAIL.

- [ ] **Step 3: Implement endpoints.py and main.py**
  Assemble FastAPI router, dependency injection for database session, static files mounting, and CORS.

- [ ] **Step 4: Run test to verify it passes**
  Run: `pytest backend/tests/test_api.py`
  Expected: PASS.

- [ ] **Step 5: Commit**
  Run: `git commit -m "feat(api): expose REST API endpoints for ingestion and reconciliation"`

---

### Task 7: React / Vite Responsive Frontend UI

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/components/Dashboard.tsx`
- Create: `frontend/src/components/IngestionCenter.tsx`
- Create: `frontend/src/components/ReconciliationView.tsx`
- Create: `frontend/src/components/TransactionsLedger.tsx`
- Create: `frontend/src/api/client.ts`
- Test: Frontend build check (`npm run build`)

**Interfaces:**
- Consumes: REST API on `/api/*`.
- Produces: Compiled HTML/JS/CSS assets ready for static serving by FastAPI or Nginx.

- [ ] **Step 1: Scaffolding Vite React TypeScript application**
  Set up React 18, Tailwind CSS, Lucide Icons, and Axios/Fetch client.

- [ ] **Step 2: Build Dashboard view**
  Cards for each account (BBVA, Revolut, Satispay, Directa, Amex, etc.), Net Worth total, and monthly cash flow chart.

- [ ] **Step 3: Build Ingestion Center view**
  One-click "Pull from Remote Server (192.168.1.185)" button, drag-and-drop file upload zone, and import summary modal.

- [ ] **Step 4: Build Reconciliation Diff view**
  Interactive side-by-side comparison table between Firefly III numbers and parsed statements, highlighting discrepancies with colored badges.

- [ ] **Step 5: Build Transactions Ledger view**
  Filterable table with search, account selector, category badges, and export to CSV.

- [ ] **Step 6: Build check**
  Run: `cd frontend && npm run build`
  Expected: Build succeeds with 0 errors.

- [ ] **Step 7: Commit**
  Run: `git commit -m "feat(frontend): build responsive React dashboard and reconciliation UI"`

---

### Task 8: Docker Packaging & End-to-End Local Verification

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `README.md`

**Interfaces:**
- Produces: Production Docker container running on `http://localhost:30095`.

- [ ] **Step 1: Write multi-stage Dockerfile and docker-compose.yml**
  Stage 1 builds React frontend; Stage 2 installs Python dependencies and serves backend + static frontend on port 8000 (mapped to 30095).
  Configure volumes for `./data`, `~/.ssh:ro`, and `init.sql:ro`. Peered to `firefly_net`.

- [ ] **Step 2: Build and start container**
  Run: `docker compose build && docker compose up -d`
  Expected: Container starts and reports healthy.

- [ ] **Step 3: End-to-end verification**
  Run:
  - Check `curl http://localhost:30095/api/health` returns `{"status": "ok"}`.
  - Trigger reconciliation endpoint to verify it reads Firefly data from `init.sql`.
  - Trigger remote SSH sync test against `192.168.1.185`.

- [ ] **Step 4: Final commit**
  Run: `git add . && git commit -m "chore: complete docker deployment and e2e verification"`
