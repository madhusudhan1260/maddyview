"""Decimal helpers. Intermediate maths keeps full precision; rounding happens once, at the edge."""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal, localcontext

PAISA = Decimal("0.01")
ZERO = Decimal("0")
HUNDRED = Decimal("100")
DAYS_IN_YEAR = Decimal("365")


def D(value) -> Decimal:
    """Convert to Decimal without passing through binary float."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(repr(value))
    return Decimal(str(value))


def round_money(value: Decimal) -> Decimal:
    return D(value).quantize(PAISA, rounding=ROUND_HALF_UP)


def round_pct(value: Decimal) -> Decimal:
    return D(value).quantize(PAISA, rounding=ROUND_HALF_UP)


def pow_dec(base: Decimal, exponent: Decimal) -> Decimal:
    """base ** exponent with 34 significant digits (supports fractional exponents for base > 0)."""
    with localcontext() as ctx:
        ctx.prec = 34
        return D(base) ** D(exponent)


def add_months(d: date, months: int) -> date:
    """Calendar month arithmetic; clamps to month end (31 Jan + 1 month = 28/29 Feb)."""
    y, m = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return date(year, month, day)
        except ValueError:
            continue
    raise ValueError("invalid date")  # pragma: no cover


def whole_months_between(start: date, end: date) -> int:
    """Largest n with add_months(start, n) <= end (0 if end <= start)."""
    if end <= start:
        return 0
    n = (end.year - start.year) * 12 + (end.month - start.month)
    while n > 0 and add_months(start, n) > end:
        n -= 1
    return n


def month_start(d: date) -> date:
    return d.replace(day=1)
