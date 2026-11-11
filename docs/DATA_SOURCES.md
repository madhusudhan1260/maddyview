# Data sources and provenance labels

Every financial and market record has a `source` column. It is a VARCHAR with a database
`CHECK` constraint, so an unknown label cannot be stored, even through raw SQL.

| Label | Meaning | Set by | UI treatment |
|---|---|---|---|
| `REAL` | Verified from an authoritative external provider after a successful, logged fetch | Data providers (none connected in Milestone 1) | Green "Verified" badge |
| `DEMO` | Illustrative sample data. Not the user's money and not real market data | `POST /api/v1/demo` only | Purple "DEMO" badge, tinted row, app-wide banner |
| `USER_ENTERED` | Typed in manually by the user | Every create endpoint (forced server-side) | No badge (the default) |
| `SIMULATED` | Paper-trading or simulation output | Paper-trading engine (later) | Blue "Simulated" badge |
| `AI_DERIVED` | Produced by a model; uncertain by nature | AI engine (later) | Amber "AI" badge |

## Rules enforced in Milestone 1

1. **Clients cannot choose a label.** Create endpoints ignore any `source` in the body and store
   `USER_ENTERED`. A test asserts that a client sending `"source": "REAL"` gets `USER_ENTERED`.
2. **DEMO is never silently mixed with real data.** DEMO rows are hidden by default. The
   *Show DEMO data* setting (`user_settings.include_demo_data`) controls whether lists **and**
   dashboard totals include them. While it is on:
   - an app-wide banner says DEMO data is visible,
   - the dashboard shows an "Includes DEMO data" badge,
   - every DEMO row carries a DEMO badge.
3. **DEMO content is obviously fictional.** It uses "Demo Bank (fictional)" and "DEMO Employer",
   and every DEMO deposit rate is `rate_verified = false`.
4. **DEMO data is removable in one action** (`DELETE /api/v1/demo`). This deletes only rows
   labelled DEMO.
5. **No fabricated market data.** The Mutual Funds, Stocks, Market Intelligence, Trading and
   Paper Trading pages show no numbers, and explain which verified source each one needs.
6. **Bank interest rates are never looked up or guessed.** The user enters them. Each FD/RD has
   `rate_verified`, which stays false until the user confirms the rate against the bank's
   document. Unverified rates get an amber "Unverified" badge, and the deposit summary counts
   them.
7. **Valuation honesty.** Investments are shown "At cost — no live prices" until a price
   provider exists.
8. **Projections are labelled.** Savings goals are `DETERMINISTIC` (no return assumed).
   Investment goals are `ASSUMED_RETURN`, with the user's assumed rate and a "not guaranteed"
   warning on every card.
9. **Tax is an estimate**, always shown apart from gross values (see
   [FINANCIAL_CALCULATIONS.md](FINANCIAL_CALCULATIONS.md)).

## Adding a real data provider (Milestone 2+)

Implement `app/data_providers/base.MarketDataProvider`, then:

- register the provider in `market_data_sources` (`requires_api_key`, `is_active`);
- write a `data_ingestion_logs` row for every run (RUNNING, then SUCCESS or FAILED, with a count);
- label rows `REAL` only after a successful authenticated fetch;
- raise `ProviderNotConfigured` instead of returning guesses when credentials are missing;
- add tests that hit the provider only when credentials are present. Never claim an
  integration works without a recorded successful call.
