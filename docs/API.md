# API reference (v1)

Base path: `/api/v1`. Interactive docs: `/api/v1/docs` (Swagger) and `/api/v1/redoc`.
Machine-readable spec: [openapi.json](openapi.json), regenerated from the running code.

## Conventions

- **Auth:** an HttpOnly session cookie (`finpilot_session`) set by `/auth/register` or
  `/auth/login`. Every endpoint except `health`, `meta`, `data-sources/labels` and `auth/*`
  returns `401` without it.
- **Money:** strings with two decimals, both in (`"1500.50"`, at most 2 dp) and out. Percentages
  are strings. Dates are ISO `YYYY-MM-DD`. Month filters are `YYYY-MM`.
- **PATCH** is partial. Only the fields you send change. `null` is accepted only for nullable
  fields such as `description` or `target_date`.
- **Errors** always look like this:
  ```json
  {"error": {"code": "validation_error", "message": "Invalid input",
             "details": [{"field": "amount", "message": "Input should be greater than 0"}],
             "request_id": "4f1c…"}}
  ```
  The codes are `validation_error` (422), `unauthorized` (401), `forbidden_origin` (403),
  `not_found` (404), `conflict` / `setup_complete` (409), `invalid_reference` (422),
  `rate_limited` (429) and `internal_error` (500).
- **`source`** on every record shows its provenance (see [DATA_SOURCES.md](DATA_SOURCES.md)).
  Clients cannot set it.

## Endpoints

### System
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness plus a DB check: `{status, version, database, time}` |
| GET | `/meta` | App name, environment, API version |
| GET | `/data-sources/labels` | The five provenance labels and their meaning |
| GET | `/audit-logs?limit=50` | Your recent audit entries |
| GET | `/dashboard` | Net worth, month summary, allocation, goals, recent transactions, maturities |

### Auth and settings
| Method | Path | Description |
|---|---|---|
| GET | `/auth/status` | `{setup_required, authenticated, user}` |
| POST | `/auth/register` | Create the single account (only while none exists). Rate-limited. |
| POST | `/auth/login` | Rate-limited; sets the session cookie |
| POST | `/auth/logout` | Revokes the session server-side |
| GET | `/auth/me` | Current user |
| GET / PATCH | `/settings` | `theme`, `tax_slab_percent` (null clears it), `include_demo_data` |

### Personal finance
| Method | Path | Description |
|---|---|---|
| GET | `/income?month=&category=` | List income |
| POST | `/income` | `{amount, income_source, category, record_date, description?, bank_account_id?}` |
| GET / PATCH / DELETE | `/income/{id}` | |
| GET | `/expenses?month=&category=` | List expenses |
| POST | `/expenses` | `{amount, category, record_date, payment_method, description?, bank_account_id?}` |
| GET / PATCH / DELETE | `/expenses/{id}` | |
| GET | `/income-categories`, `/expense-categories` | Distinct categories you have used |
| GET | `/finance/summary?month=YYYY-MM` | Income, expenses, savings, savings rate (null when there is no income), breakdown |
| GET | `/finance/trend?months=6` | Monthly income, expenses and savings series |
| GET | `/finance/transactions?month=&category=&kind=INCOME\|EXPENSE&limit=` | Merged history, newest first |

### Accounts
| Method | Path | Description |
|---|---|---|
| GET / POST | `/bank-accounts` | `{bank_name, account_label, account_type, last4?, balance, balance_as_of?}` |
| GET / PATCH / DELETE | `/bank-accounts/{id}` | |
| GET / POST | `/liabilities` | `{name, liability_type, lender?, outstanding_amount, interest_rate?, emi_amount?}` |
| GET / PATCH / DELETE | `/liabilities/{id}` | |

### Deposits
| Method | Path | Description |
|---|---|---|
| POST | `/fixed-deposits/calculate` | Preview only, nothing saved |
| GET / POST | `/fixed-deposits` | Each item includes `calculation` (gross, interest, payout, tax estimate, method), `interest_earned_to_date`, `days_to_maturity` |
| GET / PATCH / DELETE | `/fixed-deposits/{id}` | |
| POST | `/recurring-deposits/calculate` | Preview only |
| GET / POST | `/recurring-deposits` | `maturity_date` is derived as start + tenure |
| GET / PATCH / DELETE | `/recurring-deposits/{id}` | |
| GET | `/deposits/summary` | Active totals: current value, interest to date, projected maturity, estimated tax, unverified-rate count |
| GET | `/deposits/upcoming-maturities?days=90` | Active FDs and RDs maturing in the window |

### Goals
| Method | Path | Description |
|---|---|---|
| GET / POST | `/savings-goals` | Each item includes `projection` (DETERMINISTIC) |
| GET / PATCH / DELETE | `/savings-goals/{id}` | |
| GET / POST | `/investment-goals` | Requires `expected_annual_return_percent`; `projection` is ASSUMED_RETURN |
| GET / PATCH / DELETE | `/investment-goals/{id}` | |

### DEMO data
| Method | Path | Description |
|---|---|---|
| GET | `/demo` | `{has_demo_data, include_demo_data}` |
| POST | `/demo` | Replace your DEMO rows with a fresh labelled set and show them |
| DELETE | `/demo` | Delete every DEMO row and hide DEMO |

Total: **64 operations**.
