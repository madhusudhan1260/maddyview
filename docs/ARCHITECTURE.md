# Architecture

MaddyView is a **modular monolith**: one FastAPI process and one PostgreSQL database, organised
internally into modules with clear boundaries. A React single-page app is served by Vite in
development.

```
Browser (React SPA, :5190)
   │  same-origin /api/* (Vite proxy)        HttpOnly session cookie
   ▼
FastAPI (:8040)  ──  middleware: request id · JSON logging · Origin check · security headers · CORS
   │
   ├── api/v1/*          HTTP only: parse, authorise, call a service, shape the response
   ├── services/*        use-cases (finance, deposits, goals, dashboard, demo, auth, audit)
   │     └── calc/*      PURE financial maths: no I/O, Decimal in → Decimal out, unit-tested
   ├── repositories/*    user-scoped queries (every query filters by user_id)
   ├── models/*          SQLAlchemy ORM (29 tables)
   └── core/*            config · logging · errors · security · rate limit · clock
   │
   ▼
PostgreSQL 16  (schema owned by Alembic migrations)
```

## Layer rules

1. **Routes never do maths.** They call a service. Services call `services/calc` for anything
   numeric. A calculation can then be tested without HTTP or a database.
2. **Money is `Decimal` end to end.** The column type is `NUMERIC(18,2)`. Pydantic takes
   `Decimal` input with at most 2 decimal places. Responses serialise money as strings
   (`"1234.50"`), so JavaScript never parses it as a float. The browser converts to `Number`
   only to format values for display.
3. **Rounding happens once, at the edge.** Intermediate values keep full precision, and
   `round_money` applies ROUND_HALF_UP to the paisa.
4. **Every query is user-scoped.** `OwnedRepository` adds `user_id = :me` to every
   read/update/delete. This holds even though the app is single-user, so multi-user later
   needs no rewrite.
5. **Provenance is mandatory.** Every financial or market row has a `source` label (see
   [DATA_SOURCES.md](DATA_SOURCES.md)). The server sets it; clients cannot.
6. **Time is injectable.** `core/clock.today()` (IST) is the only source of "today", so tests
   can freeze it.

## Security

| Concern | Implementation |
|---|---|
| Password storage | Argon2id (`argon2-cffi`, t=3, m=64 MiB, p=4), transparent rehash on login |
| Sessions | 256-bit random token in an `HttpOnly`, `SameSite=Lax`, `Path=/api` cookie (`Secure` via config). Only its SHA-256 is stored (`auth_sessions`). Server-side expiry and revocation. |
| CSRF | SameSite cookie, plus middleware that rejects unsafe methods whose `Origin` is not on the allow-list |
| Registration | Single-user: open only while no account exists |
| Brute force | Sliding-window limit on `/auth/login` and `/auth/register` per client IP (default 10/min) |
| User enumeration | Same error message for unknown email and wrong password; a dummy hash equalises timing |
| Input validation | Pydantic on every body and query; DB `CHECK` constraints as a second line |
| SQL injection | ORM / bound parameters only; no string-built SQL with user input |
| Error leakage | Uniform `{"error": {code, message, details, request_id}}`; stack traces only in server logs |
| Headers | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` |
| Secrets | Environment variables only (`.env`, git-ignored). The frontend holds no secrets. |
| Audit | `audit_logs` records auth events, settings changes, every create/update/delete and DEMO load/clear |

## Frontend

- `context/AppContext` holds auth state, user settings, theme, and a `dataVersion` counter that
  makes every `useApi` hook refetch when global state such as the DEMO toggle changes.
- `components/ui.jsx` holds the design primitives (Card, Stat, Table, Badge, SourceBadge,
  Modal…). `components/FormModal.jsx` is a field-definition-driven create/edit form that every
  CRUD page reuses.
- Theme tokens are CSS variables (dark default, light alternative) mapped into Tailwind with
  `@theme inline`. Green, red and amber are reserved for positive, negative and warning.
- Tables become stacked cards below 640 px. A Playwright test checks that no page scrolls
  horizontally at 375 px.

## Planned modules and where they go

| Module | Package | Tables already in place |
|---|---|---|
| Mutual funds / stocks | `data_providers/`, `services/` | instruments, portfolios, holdings, investment_transactions |
| Market intelligence | `data_providers/`, `workers/` | news_articles, market_data_sources, data_ingestion_logs |
| AI predictions | `ai/` | model_registry, model_predictions, prediction_results |
| Paper trading | `trading/` | paper_accounts, paper_orders, paper_positions, paper_trades |
| Alerts | `workers/` | alerts |

## Known architectural risks

- **In-memory rate limiter.** Correct for one process only. Running several workers needs a
  shared store such as Redis.
- **Dashboard aggregation in Python.** Fine for one user's data volume. It may need SQL
  aggregation or caching once holdings and transaction imports grow.
- **No live valuation.** Investments are valued at cost until a verified price provider exists.
- **iCloud-synced folder.** The project lives under `~/Desktop`. If iCloud evicts files,
  `.venv`, `node_modules` or git can hang. Restore with `pip install -r requirements.txt` or
  `npm ci`.
