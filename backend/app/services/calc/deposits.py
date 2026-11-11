"""Fixed-deposit and recurring-deposit maths (pure functions, no I/O).

Conventions (documented in docs/FINANCIAL_CALCULATIONS.md):

FD, cumulative payout
    * Whole compounding periods are counted on calendar months from the start date.
    * Interest compounds at (rate / periods-per-year) for each whole period.
    * Any broken period left at maturity earns simple interest on the accrued amount, using
      actual days / 365. This is the common convention of Indian banks, but not universal.
    * SIMPLE compounding = simple interest on principal for actual days / 365.

FD, periodic payout (monthly / quarterly / half-yearly / yearly)
    * Interest is paid out, not re-invested: each whole payout period pays principal x rate x months/12.
    * A broken final period pays simple interest for actual days / 365.
    * Many banks pay a *discounted* rate on monthly payout; enter the rate your bank quotes.
    * The compounding frequency does not apply to payout deposits.

RD
    * One instalment at the start of each month for `tenure_months` months.
    * Each instalment compounds at the chosen frequency for the time it is held, using a fractional
      exponent: R x (1 + r/n) ^ (n x months_held / 12). This matches the formula used by most
      published Indian bank RD calculators (quarterly compounding).
    * SIMPLE = simple interest on each instalment for the months it is held.

Tax figures are ESTIMATES: total interest x the marginal slab the user enters. They ignore TDS
thresholds, surcharge, cess, 15G/15H, senior-citizen limits, and the year-wise accrual of interest.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.models.enums import CompoundingFrequency, PayoutType
from app.services.calc.money import (
    DAYS_IN_YEAR,
    D,
    HUNDRED,
    ZERO,
    add_months,
    pow_dec,
    round_money,
    whole_months_between,
)

MONTHS_PER_PERIOD = {
    CompoundingFrequency.MONTHLY: 1,
    CompoundingFrequency.QUARTERLY: 3,
    CompoundingFrequency.HALF_YEARLY: 6,
    CompoundingFrequency.YEARLY: 12,
}
PAYOUT_MONTHS = {
    PayoutType.MONTHLY_PAYOUT: 1,
    PayoutType.QUARTERLY_PAYOUT: 3,
    PayoutType.HALF_YEARLY_PAYOUT: 6,
    PayoutType.YEARLY_PAYOUT: 12,
}


@dataclass(frozen=True)
class TaxEstimate:
    slab_percent: Decimal | None
    estimated_tax: Decimal | None
    estimated_post_tax_interest: Decimal | None
    estimated_post_tax_value: Decimal | None
    note: str


@dataclass(frozen=True)
class FDResult:
    principal: Decimal
    tenure_days: int
    total_interest: Decimal  # gross
    gross_maturity_value: Decimal  # principal + all interest (cumulative: the maturity cheque)
    amount_at_maturity: Decimal  # what is credited on the maturity date
    periodic_payout: Decimal | None  # payout deposits only
    payout_count: int
    tax: TaxEstimate
    method: str
    assumptions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RDResult:
    monthly_installment: Decimal
    tenure_months: int
    total_deposited: Decimal
    total_interest: Decimal
    gross_maturity_value: Decimal
    tax: TaxEstimate
    method: str
    assumptions: list[str] = field(default_factory=list)


def estimate_tax(interest: Decimal, gross_value: Decimal, slab_percent: Decimal | None) -> TaxEstimate:
    if slab_percent is None:
        return TaxEstimate(None, None, None, None, "Set your income-tax slab in Settings to see an estimate.")
    tax = round_money(D(interest) * D(slab_percent) / HUNDRED)
    return TaxEstimate(
        slab_percent=D(slab_percent),
        estimated_tax=tax,
        estimated_post_tax_interest=round_money(D(interest) - tax),
        estimated_post_tax_value=round_money(D(gross_value) - tax),
        note="Estimate only: interest x your slab. Ignores TDS rules, surcharge, cess and exemptions.",
    )


def _validate(rate: Decimal, start: date, end: date) -> None:
    if D(rate) < 0:
        raise ValueError("interest rate cannot be negative")
    if end <= start:
        raise ValueError("maturity date must be after start date")


def fd_interest_until(
    principal, rate_percent, start: date, end: date, compounding: CompoundingFrequency, payout: PayoutType
) -> tuple[Decimal, Decimal | None, int, Decimal]:
    """Unrounded (total_interest, periodic_payout, payout_count, broken_period_interest) from start to end."""
    p, r = D(principal), D(rate_percent) / HUNDRED
    if end <= start:
        return ZERO, None, 0, ZERO

    if payout != PayoutType.CUMULATIVE:
        pm = PAYOUT_MONTHS[payout]
        count = whole_months_between(start, end) // pm
        stub_days = (end - add_months(start, count * pm)).days
        per_period = p * r * pm / 12
        stub = p * r * stub_days / DAYS_IN_YEAR
        return per_period * count + stub, per_period, count, stub

    if compounding == CompoundingFrequency.SIMPLE:
        return p * r * (end - start).days / DAYS_IN_YEAR, None, 0, ZERO

    mpp = MONTHS_PER_PERIOD[compounding]
    periods = whole_months_between(start, end) // mpp
    stub_days = (end - add_months(start, periods * mpp)).days
    amount = p * pow_dec(1 + r * mpp / 12, periods)
    stub = amount * r * stub_days / DAYS_IN_YEAR
    return amount + stub - p, None, 0, stub


def fd_maturity(
    principal,
    rate_percent,
    start: date,
    maturity: date,
    compounding: CompoundingFrequency,
    payout: PayoutType,
    tax_slab_percent=None,
) -> FDResult:
    _validate(rate_percent, start, maturity)
    p = D(principal)
    if p <= 0:
        raise ValueError("principal must be positive")
    interest, per_period, count, stub = fd_interest_until(p, rate_percent, start, maturity, compounding, payout)
    total_interest = round_money(interest)
    gross = round_money(p + total_interest)

    assumptions = ["Rate is as entered by you; confirm it against the bank's deposit receipt."]
    if payout == PayoutType.CUMULATIVE:
        if compounding == CompoundingFrequency.SIMPLE:
            method = "Simple interest on principal for actual days / 365."
        else:
            method = (
                f"{compounding.value.replace('_', '-').capitalize()} compounding on whole periods, "
                "simple interest (actual/365) on any broken period."
            )
        at_maturity = gross
        periodic = None
    else:
        method = f"Interest paid out every {PAYOUT_MONTHS[payout]} month(s) as simple interest; principal returned at maturity."
        assumptions.append("Compounding frequency does not apply to payout deposits.")
        if payout == PayoutType.MONTHLY_PAYOUT:
            assumptions.append("Banks often pay a discounted rate on monthly payout — enter the rate your bank quotes.")
        at_maturity = round_money(p + stub)
        periodic = round_money(per_period)

    return FDResult(
        principal=round_money(p),
        tenure_days=(maturity - start).days,
        total_interest=total_interest,
        gross_maturity_value=gross,
        amount_at_maturity=at_maturity,
        periodic_payout=periodic,
        payout_count=count,
        tax=estimate_tax(total_interest, gross, tax_slab_percent),
        method=method,
        assumptions=assumptions,
    )


def fd_accrued_interest(principal, rate_percent, start, maturity, compounding, payout, as_of: date) -> Decimal:
    """Gross interest earned (accrued or paid out) from start up to min(as_of, maturity)."""
    end = min(as_of, maturity)
    interest, *_ = fd_interest_until(principal, rate_percent, start, end, compounding, payout)
    return round_money(interest)


def _installment_value(installment: Decimal, r: Decimal, compounding: CompoundingFrequency, months_held: Decimal) -> Decimal:
    if compounding == CompoundingFrequency.SIMPLE:
        return installment * (1 + r * months_held / 12)
    mpp = MONTHS_PER_PERIOD[compounding]
    n = Decimal(12) / mpp
    return installment * pow_dec(1 + r / n, n * months_held / 12)


def rd_maturity(
    monthly_installment,
    rate_percent,
    tenure_months: int,
    compounding: CompoundingFrequency,
    tax_slab_percent=None,
) -> RDResult:
    inst, r = D(monthly_installment), D(rate_percent) / HUNDRED
    if inst <= 0:
        raise ValueError("instalment must be positive")
    if tenure_months <= 0:
        raise ValueError("tenure must be at least one month")
    if r < 0:
        raise ValueError("interest rate cannot be negative")

    value = sum(
        (_installment_value(inst, r, compounding, Decimal(tenure_months - i)) for i in range(tenure_months)), ZERO
    )
    deposited = round_money(inst * tenure_months)
    gross = round_money(value)
    interest = round_money(gross - deposited)
    if compounding == CompoundingFrequency.SIMPLE:
        method = "Simple interest on each monthly instalment for the months it is held."
    else:
        method = f"Each instalment compounds {compounding.value.replace('_', '-').lower()} for the time it is held (fractional-period formula)."
    return RDResult(
        monthly_installment=round_money(inst),
        tenure_months=tenure_months,
        total_deposited=deposited,
        total_interest=interest,
        gross_maturity_value=gross,
        tax=estimate_tax(interest, gross, tax_slab_percent),
        method=method,
        assumptions=[
            "Assumes every instalment is paid on time at the start of each month (no penalties).",
            "Rate is as entered by you; confirm it against the bank's RD receipt.",
        ],
    )


def rd_progress(monthly_installment, rate_percent, start: date, tenure_months: int, compounding, as_of: date) -> tuple[Decimal, Decimal]:
    """(amount deposited so far, gross interest accrued so far) as of a date, assuming on-time instalments."""
    inst, r = D(monthly_installment), D(rate_percent) / HUNDRED
    if as_of < start:
        return ZERO, ZERO
    maturity = add_months(start, tenure_months)
    end = min(as_of, maturity)
    paid = min(whole_months_between(start, end) + (1 if end < maturity else 0), tenure_months)
    deposited = ZERO
    value = ZERO
    for i in range(paid):
        deposited += inst
        days_held = Decimal((end - add_months(start, i)).days)
        months_held = days_held * 12 / DAYS_IN_YEAR
        value += _installment_value(inst, r, compounding, months_held)
    return round_money(deposited), round_money(value - deposited)
