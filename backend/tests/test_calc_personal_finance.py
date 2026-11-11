from decimal import Decimal as D

from app.services.calc.personal_finance import expense_breakdown, monthly_summary, savings_rate, total


def test_totals_use_exact_decimal_arithmetic():
    # 0.1 + 0.2 is 0.30000000000000004 in binary float; must be exactly 0.30 here
    assert total([D("0.10"), D("0.20")]) == D("0.30")
    assert total([]) == D("0.00")


def test_monthly_savings_and_rate():
    s = monthly_summary([D("50000"), D("25000")], [("Rent", D("20000")), ("Food", D("10000.50"))])
    assert s.total_income == D("75000.00")
    assert s.total_expenses == D("30000.50")
    assert s.savings == D("44999.50")
    assert s.savings_rate == D("60.00")  # 44999.5 / 75000 = 59.9993 -> 60.00


def test_negative_savings_when_overspending():
    s = monthly_summary([D("10000")], [("Rent", D("12500"))])
    assert s.savings == D("-2500.00")
    assert s.savings_rate == D("-25.00")


def test_zero_income_period_is_safe():
    assert savings_rate(D("0"), D("5000")) is None
    s = monthly_summary([], [("Food", D("100"))])
    assert s.savings == D("-100.00")
    assert s.savings_rate is None


def test_empty_month():
    s = monthly_summary([], [])
    assert (s.total_income, s.total_expenses, s.savings, s.savings_rate) == (D("0.00"), D("0.00"), D("0.00"), None)
    assert s.expense_breakdown == []


def test_expense_breakdown_groups_sorts_and_rounds():
    rows = expense_breakdown([("Food", D("100")), ("Rent", D("200")), ("Food", D("33.333"))])
    assert [r.category for r in rows] == ["Rent", "Food"]
    assert rows[1].amount == D("133.33")
    assert rows[0].percent == D("60.00")
    assert rows[1].percent == D("40.00")


def test_rounding_half_up():
    assert total([D("0.005")]) == D("0.01")
    assert total([D("0.004")]) == D("0.00")
