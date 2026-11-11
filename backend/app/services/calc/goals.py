"""Goal progress and projections (pure functions).

Savings goals are DETERMINISTIC: contributions only, no return assumed.
Investment goals are PROJECTIONS: they rely on a user-supplied annual return that is not
guaranteed and can be negative in reality. The UI must present them as such.
"""

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.services.calc.money import D, HUNDRED, ZERO, add_months, pow_dec, round_money, round_pct, whole_months_between

MAX_PROJECTION_MONTHS = 1200  # 100 years — beyond this we report "not reachable"


@dataclass(frozen=True)
class GoalProjection:
    progress_percent: Decimal
    remaining_amount: Decimal
    months_to_goal: int | None  # None = not reachable with current inputs
    estimated_completion_date: date | None
    required_monthly_contribution: Decimal | None  # to hit target_date; None without a target date
    on_track: bool | None  # None without a target date
    projection_type: str  # "DETERMINISTIC" | "ASSUMED_RETURN"
    assumption: str


def progress_percent(current, target) -> Decimal:
    target = D(target)
    if target <= 0:
        raise ValueError("target must be positive")
    pct = D(current) / target * HUNDRED
    return round_pct(min(max(pct, ZERO), HUNDRED))


def monthly_rate_from_annual(annual_percent) -> Decimal:
    """Effective monthly rate equivalent to an annual compound rate."""
    a = D(annual_percent) / HUNDRED
    if a <= -1:
        raise ValueError("annual return must be greater than -100%")
    return pow_dec(1 + a, Decimal(1) / 12) - 1


def _months_until(today: date, target_date: date | None) -> int | None:
    if target_date is None:
        return None
    return max(whole_months_between(today, target_date), 0)


def project_savings_goal(target, current, monthly_contribution, today: date, target_date: date | None = None) -> GoalProjection:
    target, current, contrib = D(target), D(current), D(monthly_contribution)
    remaining = max(target - current, ZERO)
    if remaining == 0:
        months = 0
    elif contrib > 0:
        months = math.ceil(remaining / contrib)
    else:
        months = None

    months_left = _months_until(today, target_date)
    required = None
    if months_left is not None:
        required = round_money(remaining) if months_left == 0 else round_money(remaining / months_left)

    return GoalProjection(
        progress_percent=progress_percent(current, target),
        remaining_amount=round_money(remaining),
        months_to_goal=months,
        estimated_completion_date=add_months(today, months) if months is not None else None,
        required_monthly_contribution=required,
        on_track=None if months_left is None else (months is not None and months <= months_left),
        projection_type="DETERMINISTIC",
        assumption="Assumes no interest or return; only your monthly contributions count.",
    )


def future_value(current, monthly_contribution, monthly_rate: Decimal, months: int) -> Decimal:
    """Balance after `months` with contributions at the end of each month."""
    bal = D(current)
    for _ in range(months):
        bal = bal * (1 + monthly_rate) + D(monthly_contribution)
    return bal


def project_investment_goal(
    target, current, monthly_contribution, annual_return_percent, today: date, target_date: date | None = None
) -> GoalProjection:
    target, current, contrib = D(target), D(current), D(monthly_contribution)
    m = monthly_rate_from_annual(annual_return_percent)
    remaining = max(target - current, ZERO)

    months: int | None = 0
    if remaining > 0:
        bal, months = current, None
        for i in range(1, MAX_PROJECTION_MONTHS + 1):
            bal = bal * (1 + m) + contrib
            if round_money(bal) >= target:  # compare at paisa precision
                months = i
                break

    months_left = _months_until(today, target_date)
    required = None
    if months_left is not None:
        if months_left == 0:
            required = round_money(remaining)
        elif m == 0:
            required = round_money(max(remaining / months_left, ZERO))
        else:
            growth = pow_dec(1 + m, months_left)
            needed = (target - current * growth) * m / (growth - 1)
            required = round_money(max(needed, ZERO))

    return GoalProjection(
        progress_percent=progress_percent(current, target),
        remaining_amount=round_money(remaining),
        months_to_goal=months,
        estimated_completion_date=add_months(today, months) if months is not None else None,
        required_monthly_contribution=required,
        on_track=None if months_left is None else (months is not None and months <= months_left),
        projection_type="ASSUMED_RETURN",
        assumption=(
            f"Assumes a constant {D(annual_return_percent).normalize():f}% annual return, compounded monthly. "
            "Market returns are not guaranteed, vary year to year and can be negative."
        ),
    )
