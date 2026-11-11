# MaddyView

A personal financial-intelligence platform focused on Indian markets. This repository holds
**Milestone 1: the foundation.** It covers personal finance, FD/RD tracking, financial goals,
the net-worth dashboard, authentication and a complete database schema for later modules.

> MaddyView never places real trades or moves money. Every figure shown comes from records you
> enter, or from DEMO records that are clearly labelled. No market feed, NAV, bank rate or news
> item is fabricated.

| Layer    | Stack |
|----------|-------|
| Frontend | React 18, Vite 6, Tailwind CSS 4, React Router 6, Lucide icons |
| Backend  | Python 3.13, FastAPI, SQLAlchemy 2, Pydantic 2, Alembic |
| Database | PostgreSQL 16 (money stored as `NUMERIC`, never float) |
| Tests    | Pytest + FastAPI TestClient (backend), Playwright (end-to-end) |

## Prerequisites

- Python 3.13 (`python3.13`)
- Node.js 20 or newer (tested on Node 26)
- PostgreSQL 16 running locally on port 5432, with the `createdb` and `psql` tools on your `PATH`

## First-time setup

```bash
cd finpilot/backend
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # edit if your Postgres URL differs
createdb finpilot
createdb finpilot_test
.venv/bin/alembic upgrade head  # creates all tables
```

```bash
cd finpilot/frontend
npm install
```

## Run locally

Start the backend first, from `finpilot/backend`:

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8040 --reload
```

Then start the frontend, from `finpilot/frontend`:

```bash
npm run dev
```

Open http://localhost:5190. The first visit asks you to create the only account. MaddyView is
single-user, and registration closes once that account exists.

- Interactive API docs: http://127.0.0.1:8040/api/v1/docs
- Health check: http://127.0.0.1:8040/api/v1/health

The browser only talks to the Vite origin. `/api` is proxied to FastAPI, so the session cookie
stays first-party and no backend address or secret ships to the client.

## Tests

Backend tests run against a real PostgreSQL test database (`finpilot_test`). It is migrated with
Alembic and truncated between tests. Run them from `finpilot/backend`:

```bash
.venv/bin/python -m pytest -q
```

End-to-end tests start an **isolated** stack: the API on port 8041 with a throwaway
`finpilot_e2e` database, and Vite on port 5191. They never touch your real database. Run them
from `finpilot/frontend`:

```bash
npx playwright install chromium   # first time only
npm run test:e2e
```

## Project layout

```
finpilot/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers (v1) + dependencies
│   │   ├── core/           # config, logging, errors, security, rate limiting, clock
│   │   ├── database/       # engine/session, declarative base, column types
│   │   ├── models/         # SQLAlchemy models (29 tables)
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── repositories/   # user-scoped data access
│   │   ├── services/       # use-cases; services/calc = pure, tested financial maths
│   │   ├── data_providers/ # provider interface (no live provider connected yet)
│   │   ├── ai/ trading/ workers/   # reserved for later milestones
│   ├── alembic/            # migrations
│   └── tests/              # pytest suite
├── frontend/
│   ├── src/{components,context,lib,pages}
│   └── e2e/                # Playwright specs
├── scripts/e2e-api.sh      # isolated API for E2E
└── docs/                   # architecture, database, data sources, calculations, API
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Database](docs/DATABASE.md)
- [Data sources and labels](docs/DATA_SOURCES.md)
- [Financial calculations](docs/FINANCIAL_CALCULATIONS.md)
- [API reference](docs/API.md) (machine-readable: [docs/openapi.json](docs/openapi.json))
- [Milestone 1 report](docs/MILESTONE_1_REPORT.md)

## Configuration

All settings are environment variables prefixed `FINPILOT_`. They are read from `backend/.env`
(see [backend/.env.example](backend/.env.example)). `.env` is git-ignored and must never be
committed.
