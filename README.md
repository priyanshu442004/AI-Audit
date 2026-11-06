# IKIO P2P Audit Dashboard

Full-stack procure-to-pay audit tool — React + FastAPI.

## Architecture

```
backend/   FastAPI (Python) — pandas analysis, SSE progress, AI insights
frontend/  React + Vite + Tailwind — identical UI to the original index.html
```

---

## Prerequisites

| Tool    | Version |
|---------|---------|
| Python  | 3.10+   |
| Node.js | 18+     |
| npm     | 9+      |

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Set your Anthropic API key (optional — AI narrative only):

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# macOS/Linux
export ANTHROPIC_API_KEY="sk-ant-..."
```

Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

API is live at `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App opens at `http://localhost:5173`.

---

## Uploading Files

The dashboard expects up to **6 Excel / CSV files** mapped to these roles:

| Role key             | Upload label         | Contents                               |
|----------------------|----------------------|----------------------------------------|
| `vendor_master`      | Vendor Master Sheet  | Vendor code, name, MSME reg, GSTIN, PAN |
| `purchase_order`     | Purchase Order       | PO lines, qty, price, open qty         |
| `gate_entry`         | Gate Entry Report    | GE date, linked GRPO, vendor bill date |
| `grpo`               | GRPO Report          | Goods receipts vs PO                   |
| `purchase_register`  | Purchase Register    | AP invoices, due dates, payment dates  |
| `general_ledger`     | General Ledger       | Vendor debit / credit movements        |

You can upload **any subset** — sections whose source file is missing will show an empty state.

---

## Column Normalisation

Column headers are detected automatically via hundreds of aliases in `backend/app/config.py → COLUMN_ALIASES`. If a required column is missing the API returns a clear error message listing expected aliases.

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## API Endpoints

| Method | Path                          | Description                        |
|--------|-------------------------------|------------------------------------|
| POST   | `/api/upload`                 | Upload files; returns `session_id` |
| GET    | `/api/analyze/{session_id}`   | SSE stream: progress + final result|
| POST   | `/api/insights/{section}`     | AI narrative for a section         |
| GET    | `/api/result/{session_id}`    | Re-fetch stored result             |
| GET    | `/api/health`                 | Health check                       |

---

## Analysis Modules

| ID  | Module           | Rule                                            |
|-----|------------------|-------------------------------------------------|
| A   | po_status        | OPEN/CLOSED by Open Qty > 0                     |
| B   | gate_entry       | Bill ≤ GE ≤ GRPO ≤ AP date sequence             |
| C   | qty_variance     | (PO−Received)/PO; 0–5% OK, >5% flag             |
| D/E | price_variance   | (Max−Min)/Max per item; savings = (Avg−Min)×Qty |
| F   | gl_balances      | Net = Credit − Debit per vendor                 |
| G   | payment_aging    | Days Late buckets; FIFO invoice matching        |
| H   | msme             | 45-day limit for Micro/Small; 27% p.a. penalty  |
| I   | vendor_master    | Duplicate names, invalid GSTIN/PAN              |
| J   | three_way        | PO ↔ GRPO ↔ Invoice within 5% tolerance        |

---

## Configuration Constants (`backend/app/config.py`)

```python
VARIANCE_TOLERANCE_PCT  = 5.0   # qty & price threshold
MSME_PAYMENT_LIMIT_DAYS = 45    # MSMED Act §16
MSME_PENALTY_RATE_PA    = 0.27  # 27% p.a. (3× RBI Bank Rate 9%)
SERVICES_ITEM_PREFIX    = "SV"  # Item code prefix for services
```

---

## Daily P2P Management Summary

The management report copies KPI values and charts from the same PO status and
gate-entry API response payloads consumed by the dashboard, plus the Stock
Verified Report API response used by its dashboard section. It does not rerun
those analyses to produce report KPI values and does not include Vendor Price
Comparison Analysis. The permanent KPI names, complete descriptions, source
references and formatting metadata are in
`backend/app/kpi_service/kpi_definitions.py`. Missing source values remain
unavailable; they are not converted to zero. The report is not sent when a
required dashboard KPI or reporting date is missing.

### Configure and run

1. Copy `.env.example` to `.env` and retain the existing PostgreSQL, S3 and app
   settings. Never commit `.env` or paste credentials into source files.
2. Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` and `MAIL_FROM` using
   your organization's approved SMTP relay. Create an app-specific SMTP
   credential if the provider requires one, verify that the sender address is
   authorized, and confirm the relay permits the two configured recipients.
   The application sends a separate message per recipient so delivery is tracked
   independently.
3. Keep `KPI_EMAIL_RECIPIENTS` as a comma-separated list of addresses. The
   provided defaults are the management recipients requested for this report.
4. Set `KPI_ADMIN_TOKEN` to a generated high-entropy secret. For example, run
   `python -c "import secrets; print(secrets.token_urlsafe(32))"` and store the
   output only in the backend environment. The Settings > Management Report panel
   requires this token for status, history, downloads and manual execution.
5. Install the backend requirements, including the PDF renderer and persistent
   scheduler:

   ```powershell
   cd backend
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

6. Configure `KPI_REPORT_ENTITY` (`ITL` or `ISPL`), then start the normal FastAPI
   service. The report uses the same active source files and dashboard analysis
   functions without an additional report-only date filter. The scheduler uses
   `KPI_SCHEDULE_CRON` and `KPI_SCHEDULE_TIMEZONE`; the default is 9:00 AM
   Asia/Kolkata each day.
   Keep the service running at the scheduled time. The scheduler's job records
   are stored in PostgreSQL; unique execution and per-recipient local delivery
   date claims coordinate multiple instances and prevent more than one email per
   recipient per day. A manual test send counts toward that day's delivery.
   Failed recipient deliveries are retried without resending to recipients
   already marked sent.
7. Configure `KPI_PDF_OUTPUT_DIR` and `KPI_PDF_TEMP_DIR` only if the defaults
   (backend `generated_reports` and the operating-system temporary directory)
   are not suitable. Ensure the service account can write to both.
8. Use a safe SMTP capture server and test recipients in a non-production
   environment before enabling real delivery. Do not validate by sending to the
   configured management recipients.

The PDF contains exactly three pages. Its KPI values and charts are copied from
the dashboard API responses; the report does not apply its own financial-year,
transaction-date, inventory snapshot, or Purchase Register filters. The
displayed period and financial-year label are derived from source transaction
dates (not planned delivery dates or historical GRN reference dates). Stock
verification uses the dashboard's Stock Verified Report response and is
identified as an as-of snapshot in the email. Each KPI's full description is
wrapped inside its card.
Historical comparisons and targets are not invented where the source data does
not provide them. The PDF and email interpretations are deterministic. DeepSeek settings are reserved but unused:
no KPI, transaction, or management data is transmitted to an external AI
service.

### Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Existing PostgreSQL connection; stores report history and APScheduler jobs. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME` | Existing S3 access used to load the latest uploaded report files. |
| `SMTP_HOST` | Organization-approved SMTP host. Required for delivery. |
| `SMTP_PORT` | SMTP port; defaults to 465 (implicit TLS). Other configured ports use STARTTLS. |
| `SMTP_USER`, `SMTP_PASS` | SMTP account credentials; set both or leave both blank for an authenticated network relay. |
| `MAIL_FROM` | Verified sender address shown on management emails. |
| `KPI_EMAIL_RECIPIENTS` | Comma-separated recipient addresses; defaults to the two requested management addresses. |
| `KPI_SCHEDULER_ENABLED` | Enables the scheduled daily workflow; defaults to `true`. |
| `KPI_SCHEDULE_CRON` | Five-field cron expression; defaults to `0 9 * * *`. |
| `KPI_SCHEDULE_TIMEZONE` | Scheduler timezone; defaults to `Asia/Kolkata`. |
| `KPI_REPORT_ENTITY` | P2P entity whose existing source files are used; `ITL` by default. |
| `KPI_ADMIN_TOKEN` | Required server-side secret for administrator report endpoints; never expose it in frontend build configuration. |
| `KPI_PDF_OUTPUT_DIR` | Optional persistent output directory; defaults to `backend/generated_reports`. |
| `KPI_PDF_TEMP_DIR` | Optional directory for transient PDF staging; defaults to the system temporary directory. |
| `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL` | Reserved optional settings; not used by this implementation, which deliberately keeps report data local. |
| `ANTHROPIC_API_KEY`, `BACKEND_URL` | Existing application settings, unrelated to the daily report delivery. |
