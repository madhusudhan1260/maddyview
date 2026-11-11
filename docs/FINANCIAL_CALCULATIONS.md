# Financial calculations

All maths lives in `backend/app/services/calc/` as pure functions on `Decimal`. Intermediate
values keep full precision, using a 34-digit context for powers. Results are rounded once to the
paisa with ROUND_HALF_UP. Every formula below has tests in `backend/tests/test_calc_*.py`.

## Personal finance

```
Monthly Savings = Monthly Income − Monthly Expenses        (may be negative)
Savings Rate    = Monthly Savings ÷ Monthly Income × 100
```

- **Zero-income months:** the savings rate is `null`, never 0 and never ∞. The API adds
  `savings_rate_note`, and the UI shows "No income recorded".
- The expense breakdown groups by category and sorts by amount. Each category's percent is its
  share of total expenses.
- A month filter covers `[first day, first day of next month)`.

## Fixed deposits

Inputs: principal *P*, annual rate *r* (as entered), start and maturity dates, compounding
frequency, and payout type. **The dates are authoritative.** `tenure_months` is informational.

### Cumulative (interest re-invested)

| Compounding | Method |
|---|---|
| Monthly / Quarterly / Half-yearly / Yearly | Count *whole* compounding periods in calendar months from the start date: `A = P × (1 + r/n)^k`. Any broken period left at maturity earns simple interest `A × r × days/365`. |
| Simple | `P × r × days/365` |

Reference check: ₹1,00,000 at 7% quarterly for 1 year comes to **₹1,07,185.90**, matching the
standard `P(1 + r/4)^4`.

### Payout (monthly / quarterly / half-yearly / yearly)

Interest is paid out and not re-invested. Each whole payout period pays `P × r × months/12`. A
broken final period pays `P × r × days/365`. The principal comes back at maturity. The
compounding frequency does not apply.

> Many Indian banks pay a **discounted** rate on monthly-payout FDs. MaddyView does not apply a
> discount. Enter the rate your bank quotes for the payout option.

### Interest earned to date

The same formula is applied with the end date `min(today, maturity)`. For payout FDs this is
interest paid or accrued so far. For cumulative FDs it is accrued value.

## Recurring deposits

There is one instalment *R* at the start of each month for *N* months. Instalment *i* is held
for `N − i` months. With compounding *n* times a year:

```
M = Σ R × (1 + r/n)^(n × months_held/12)        (fractional exponent)
```

This equals the closed form used by most published Indian bank RD calculators (quarterly):
`M = R × [(1+i)^q − 1] / (1 − (1+i)^(−1/3))`, where *i* = r/4 and *q* = quarters. Reference:
₹1,000/month at 7% for 12 months gives **₹12,462.13**. *Simple* compounding gives
`R × r × months_held/12` per instalment.

The maturity date is always `start + N months`. A supplied `maturity_date` must match it.
Progress to date assumes every instalment is paid on time.

## Tax estimate (FD and RD)

```
Estimated tax            = total interest × your marginal slab %
Estimated post-tax value = gross maturity value − estimated tax
```

The slab is set in Settings. Without a slab, no tax figure is shown. **Gross and post-tax values
are always shown separately and labelled.** The estimate ignores TDS thresholds, surcharge, cess,
Form 15G/15H, senior-citizen limits and the year-by-year accrual of interest. It is not tax advice.

## Goals

```
Progress % = min(current ÷ target, 1) × 100
```

### Savings goals: deterministic

- `months = ceil((target − current) ÷ monthly_contribution)`. The goal is unreachable if the
  contribution is 0.
- `estimated completion = today + months`
- With a target date: `required monthly = remaining ÷ whole months left`. The goal is "on track"
  if `months ≤ months left`.

### Investment goals: assumed return

- The user supplies an assumed annual return *a*, between −50% and +50%. The effective monthly
  rate is `m = (1 + a)^(1/12) − 1`.
- The projection simulates month by month, `balance = balance × (1+m) + contribution`, until it
  reaches the target (at paisa precision). Anything beyond 100 years counts as unreachable.
- The required monthly contribution for a target date uses the annuity formula
  `(target − current × (1+m)^k) × m ÷ ((1+m)^k − 1)`, or the savings formula when *m* = 0.
- Every response carries `projection_type: "ASSUMED_RETURN"` and an assumption sentence stating
  that returns are not guaranteed and can be negative.

## Dashboard

| Figure | Definition |
|---|---|
| Total assets | bank balances + active FD current value + active RD (deposited + accrued) + holdings at cost |
| Total liabilities | Σ outstanding amounts |
| Net worth | assets − liabilities |
| FD current value | cumulative: principal + accrued interest. Payout: principal. |
| Investments | quantity × average cost (**at cost**; no live prices) |
| Goal progress | Σ min(current, target) ÷ Σ target across active and achieved goals |
| Allocation | each asset class ÷ total assets |
