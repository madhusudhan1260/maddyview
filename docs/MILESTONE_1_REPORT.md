# Milestone 1 completion report

Date: 11 Nov 2026. Environment: macOS, Python 3.13.5, Node 26.9, PostgreSQL 16.15.

## 1. Files created

There are 107 project files (excluding `node_modules`, `.venv` and caches), all new; there was no
prior MaddyView code.

- **Backend (73):** `app/` (core 7, database 3, models 9, schemas 6, repositories 2, services 12,
  api 9, provider/ai/trading/workers stubs 5), one Alembic migration plus its env/config, 9 test
  modules, `requirements.txt`, `.env.example`.
- **Frontend (22):** Vite/Tailwind config, `src/` (11 pages, 3 components, context, lib), and
  the Playwright config with its specs.
- **Docs (7):** README, ARCHITECTURE, DATABASE, DATA_SOURCES, FINANCIAL_CALCULATIONS, API,
  openapi.json. **Scripts (1):** `scripts/e2e-api.sh`.

## 2. Architecture implemented

A modular-monolith FastAPI app with the layers api → services (→ pure `calc`) →
repositories → models. It has environment-based config, JSON structured logging with request
ids, a uniform error envelope, API versioning (`/api/v1`), and Argon2id plus server-side cookie
sessions. Origin checking protects against CSRF, login and register are rate-limited, every
change is audited, and money is stored as `NUMERIC`. The frontend is a React SPA behind a Vite
proxy, with a dark theme by default plus a light theme and responsive layouts. See
[ARCHITECTURE.md](ARCHITECTURE.md).

## 3. Database tables created (29, via Alembic)

users, user_settings, auth_sessions · bank_accounts, income_records, expense_records,
transactions, liabilities, monthly_budgets · instruments, portfolios, holdings,
investment_transactions · fixed_deposits, recurring_deposits · savings_goals, investment_goals ·
news_articles, market_data_sources, data_ingestion_logs · model_registry, model_predictions,
prediction_results · paper_accounts, paper_orders, paper_positions, paper_trades · audit_logs,
alerts.

Three tables were added beyond the brief, each as a stated assumption:

- `auth_sessions`, for server-side session security;
- `liabilities`, because the dashboard needs total liabilities and the brief listed no table
  for them;
- the `transactions` table is kept as a bank ledger reserved for statement import. Income and
  expense history comes from `income_records` and `expense_records`.

## 4. API endpoints

There are 64 operations. The full list is in [API.md](API.md).

## 5. Features working (verified by tests and in the browser)

- Account setup (single user), login, logout, session expiry, theme saved to the account.
- Income and expense CRUD with month and category filters, monthly summary, savings and savings
  rate (null-safe for zero income), expense breakdown, 6-month trend and a merged transaction
  history.
- Bank accounts and liabilities CRUD, feeding net worth.
- FD and RD CRUD with maturity calculation across 5 compounding modes and 5 payout modes, a live
  calculation preview, interest earned to date, totals, an upcoming-maturity list, an estimated
  tax shown apart from gross values, and unverified-rate flags.
- Savings goals (deterministic) and investment goals (assumed return, labelled) with progress,
  estimated completion, required monthly contribution and an on-track flag.
- A dashboard with all 12 requested blocks. Each has an empty state. AI reports stays an honest
  empty state.
- DEMO data that can be loaded, shown, hidden and removed, labelled everywhere and bannered.
- Honest placeholder pages for Mutual Funds, Stocks, Trading, Paper Trading and Market
  Intelligence. They show no numbers.

## 6. Tests executed and actual results

| Suite | Command | Result |
|---|---|---|
| Backend (pytest, real PostgreSQL) | `.venv/bin/python -m pytest -q` | **91 passed** in 24.4 s |
| End-to-end (Playwright, Chromium 143, isolated stack started by Playwright) | `CI=1 npx playwright test` | **8 passed** in 26.0 s |
| Migration drift | `alembic check` | "No new upgrade operations detected" |
| Migration round-trip | `upgrade head → downgrade base → upgrade head` | OK (the pytest session also does this on every run) |
| Production build | `vite build` | OK (263 kB JS / 79 kB gzip) |

Backend coverage by area: income, expense and savings maths (7 tests), FD/RD maths (25), goal
projections (11), auth and security (12), finance API and CRUD (12), deposits and goals API (9),
dashboard, DEMO separation, audit and DB relationships/constraints (15).

There were failures during development, all fixed: a goal projection was off by one month
because a Decimal power fell 1e-30 short of the target, a constraint test expected the wrong
exception type, and several E2E selectors were ambiguous.

The last run's first E2E pass failed one test. Its locator matched the hidden phone layout. The
selector was fixed and the full suite re-run green.

## 7. Known limitations

- No live market data, NAVs, prices or news (by design until Milestone 2). Investments are
  valued at cost, and no UI exists yet to add holdings.
- Tax is a rough slab estimate. It ignores TDS rules, surcharge, cess and exemptions, and
  interest accrual across tax years.
- FD conventions (whole periods plus a simple-interest broken period, actual/365) and RD
  conventions (fractional quarterly) match common Indian practice, but individual banks differ.
  The bank statement is authoritative.
- Monthly-payout FDs use the rate you enter; there is no automatic discounted-rate conversion.
- The rate limiter is in-memory (single process).
- There is no password reset or change flow yet, and no 2FA. With one account, a forgotten
  password currently means resetting the database.
- Monthly budgets and the bank ledger (`transactions`) exist in the schema but have no API or UI
  yet.
- The project sits in an iCloud-synced folder. Evicted files can stall tooling.
- The desktop app's preview runner cannot read `~/Desktop`, so the servers were started from a
  shell for browser verification.

## 8. Frontend startup command

From `finpilot/frontend`:

```bash
npm run dev
```

This serves http://localhost:5190 and proxies `/api` to `127.0.0.1:8040`.

## 9. Backend startup command

From `finpilot/backend`:

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8040 --reload
```

## 10. Remaining for Milestone 2 (proposed)

1. A mutual-fund data provider (AMFI daily NAV file) with ingestion logging, `instruments`
   seeding, and REAL labels only after a successful fetch.
2. Holdings and investment-transaction CRUD (BUY, SELL, SIP), valuation at the latest verified
   NAV, XIRR and absolute returns.
3. An equity price provider (needs credentials) and TradingView Lightweight Charts.
4. Monthly budgets (API + UI) and CSV bank-statement import into `transactions`.
5. Password change and reset, session list and revoke-all, optional TOTP.
6. A background worker for maturity and goal alerts (`alerts` table).
