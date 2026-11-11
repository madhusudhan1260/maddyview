# Database

PostgreSQL 16. Alembic owns the schema: `backend/alembic/versions/`. Tables are never created by
hand or with `create_all` outside tests.

```bash
cd backend
.venv/bin/alembic upgrade head        # apply
.venv/bin/alembic downgrade -1        # roll back one
.venv/bin/alembic revision --autogenerate -m "describe change"   # after editing models
.venv/bin/alembic check               # fails if models and migrations drift
```

Measured on the Milestone 1 migration: **29 tables, 38 foreign keys, 75 CHECK constraints,
14 unique constraints, 99 indexes** (including primary keys). Upgrade → downgrade → upgrade runs
cleanly, and `alembic check` reports no drift.

## Conventions

- **Primary keys:** `BIGINT` identity `id`.
- **Timestamps:** `created_at` and `updated_at` (`timestamptz`, server default `now()`).
- **Money:** `NUMERIC(18,2)`. Rates: `NUMERIC(7,4)` (% p.a.). Unit quantities:
  `NUMERIC(20,6)`. Prices/NAV: `NUMERIC(18,4)`. No `float`/`double` column holds money.
- **Enumerations:** `VARCHAR(32)` + `CHECK (col IN (...))`. These are easier to evolve than
  native PG enums.
- **Provenance:** `source` column with a CHECK over
  `REAL | DEMO | USER_ENTERED | SIMULATED | AI_DERIVED`, indexed.
- **Deterministic constraint names** (`pk_`, `fk_`, `uq_`, `ck_`, `ix_`) keep migrations stable.
- **Ownership:** user-owned tables have `user_id → users.id ON DELETE CASCADE` and an index.

## Tables

### Users and configuration

| Table | Purpose | Key constraints |
|---|---|---|
| `users` | The single account | `email` unique; `password_hash` (Argon2id) |
| `user_settings` | Theme, currency, tax slab, DEMO toggle | 1:1 with users (unique `user_id`); slab 0–50 |
| `auth_sessions` | Server-side sessions | `token_hash` (SHA-256) unique; `expires_at`, `revoked_at` |

### Personal finance

| Table | Purpose | Key constraints |
|---|---|---|
| `bank_accounts` | Manually tracked balances | `last4` must be 4 digits (full numbers are never stored) |
| `income_records` | Amount, income source, category, date, description | `amount > 0`; index (user_id, record_date) |
| `expense_records` | Amount, category, date, payment method, description | `amount > 0`; indexes on (user, date) and (user, category) |
| `transactions` | Bank-ledger lines (reserved for statement import) | `amount > 0`; direction CREDIT/DEBIT; optional links to income/expense |
| `liabilities` | Loans and card balances (feeds net worth) | `outstanding ≥ 0` |
| `monthly_budgets` | Per-category monthly budget (schema only) | unique (user, month, category); `month` is the 1st |

`income_records.bank_account_id` and `expense_records.bank_account_id` use `ON DELETE SET NULL`.
Deleting an account keeps your history.

### Deposits

| Table | Key constraints |
|---|---|
| `fixed_deposits` | principal > 0; rate 0–30; `maturity_date > start_date`; compounding, payout and status enums; `rate_verified` |
| `recurring_deposits` | installment > 0; tenure > 0; `maturity_date > start_date` (the API derives it as start + tenure) |

### Goals

| Table | Notes |
|---|---|
| `savings_goals` | target > 0, current ≥ 0, contribution ≥ 0 |
| `investment_goals` | as above, plus `expected_annual_return_percent` (−50…50, a user assumption) and optional `linked_portfolio_id` |

### Investments (schema only in Milestone 1)

| Table | Notes |
|---|---|
| `instruments` | Security master shared across users; unique (type, symbol, exchange); unique ISIN; AMFI `scheme_code` |
| `portfolios` | unique (user, name) |
| `holdings` | unique (portfolio, instrument); instrument FK is `RESTRICT` |
| `investment_transactions` | BUY/SELL/SIP/DIVIDEND/SWITCH; non-negative qty, price, fees |

### Market research, AI, paper trading, system (schema only)

`market_data_sources`, `data_ingestion_logs`, `news_articles` (unique URL),
`model_registry` (unique name+version, JSONB metrics), `model_predictions` (confidence 0–1,
default source `AI_DERIVED`), `prediction_results` (1:1 with prediction),
`paper_accounts` / `paper_orders` (LIMIT orders need `limit_price`) / `paper_positions` /
`paper_trades` (default source `SIMULATED`), `audit_logs` (JSONB details, indexed by time and
entity), `alerts`.

## Relationships tested

`tests/test_dashboard_and_db.py` verifies:

- deleting a user cascades to settings, accounts and records;
- deleting a bank account nulls the link on income/expense rows;
- a `holdings` row is unique per (portfolio, instrument);
- an instrument that is in use cannot be deleted;
- CHECK constraints reject a negative principal, maturity before start, a rate over 30% and an
  unknown source (raw SQL included);
- `NUMERIC` columns round-trip `0.10 + 0.20 = 0.30` exactly.
