"""Income / expense / savings maths (pure functions, no I/O)."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from app.services.calc.money import D, HUNDRED, ZERO, round_money, round_pct


@dataclass(frozen=True)
class CategoryShare:
    category: str
    amount: Decimal
    percent: Decimal  # share of total expenses


@dataclass(frozen=True)
class MonthlySummary:
    total_income: Decimal
    total_expenses: Decimal
    savings: Decimal  # Monthly Savings = Monthly Income - Monthly Expenses (can be negative)
    savings_rate: Decimal | None  # (Savings / Income) * 100; None when income is zero
    income_count: int
    expense_count: int
    expense_breakdown: list[CategoryShare] = field(default_factory=list)


def total(amounts: Iterable) -> Decimal:
    return round_money(sum((D(a) for a in amounts), ZERO))


def savings_rate(income: Decimal, expenses: Decimal) -> Decimal | None:
    """Return None (not 0, not infinity) for zero-income periods so the UI can say 'no income recorded'."""
    income, expenses = D(income), D(expenses)
    if income <= ZERO:
        return None
    return round_pct((income - expenses) / income * HUNDRED)


def expense_breakdown(expenses: Iterable[tuple[str, Decimal]]) -> list[CategoryShare]:
    by_cat: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for category, amount in expenses:
        by_cat[category] += D(amount)
    grand = sum(by_cat.values(), ZERO)
    rows = [
        CategoryShare(cat, round_money(amt), round_pct(amt / grand * HUNDRED) if grand > 0 else ZERO)
        for cat, amt in by_cat.items()
    ]
    return sorted(rows, key=lambda r: (-r.amount, r.category))


def monthly_summary(incomes: list[Decimal], expenses: list[tuple[str, Decimal]]) -> MonthlySummary:
    inc = total(incomes)
    exp = total(a for _, a in expenses)
    return MonthlySummary(
        total_income=inc,
        total_expenses=exp,
        savings=round_money(inc - exp),
        savings_rate=savings_rate(inc, exp),
        income_count=len(incomes),
        expense_count=len(expenses),
        expense_breakdown=expense_breakdown(expenses),
    )
