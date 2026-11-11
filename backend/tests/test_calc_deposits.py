from datetime import date
from decimal import Decimal as D

import pytest

from app.models.enums import CompoundingFrequency as CF
from app.models.enums import PayoutType as PT
from app.services.calc.deposits import fd_accrued_interest, fd_maturity, rd_maturity, rd_progress
from app.services.calc.money import add_months, whole_months_between


# ---------- date helpers ----------
def test_add_months_clamps_to_month_end():
    assert add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert add_months(date(2025, 11, 15), 3) == date(2026, 2, 15)
    assert add_months(date(2025, 3, 15), -3) == date(2024, 12, 15)


def test_whole_months_between():
    assert whole_months_between(date(2025, 1, 15), date(2025, 4, 14)) == 2
    assert whole_months_between(date(2025, 1, 15), date(2025, 4, 15)) == 3
    assert whole_months_between(date(2025, 1, 15), date(2025, 1, 1)) == 0


# ---------- FD ----------
def test_fd_quarterly_cumulative_one_year_matches_standard_formula():
    # 1,00,000 @ 7% quarterly for 1 year = 100000 * (1.0175)^4 = 107,185.90
    r = fd_maturity(D("100000"), D("7"), date(2025, 1, 1), date(2026, 1, 1), CF.QUARTERLY, PT.CUMULATIVE)
    assert r.gross_maturity_value == D("107185.90")
    assert r.total_interest == D("7185.90")
    assert r.amount_at_maturity == r.gross_maturity_value
    assert r.periodic_payout is None


@pytest.mark.parametrize("freq,expected", [
    (CF.MONTHLY, D("107229.01")),   # (1 + .07/12)^12
    (CF.HALF_YEARLY, D("107122.50")),  # (1.035)^2
    (CF.YEARLY, D("107000.00")),
])
def test_fd_other_compounding_frequencies(freq, expected):
    r = fd_maturity(D("100000"), D("7"), date(2025, 1, 1), date(2026, 1, 1), freq, PT.CUMULATIVE)
    assert r.gross_maturity_value == expected


def test_fd_simple_interest_uses_actual_days():
    r = fd_maturity(D("100000"), D("7"), date(2025, 1, 1), date(2025, 7, 1), CF.SIMPLE, PT.CUMULATIVE)
    assert r.tenure_days == 181
    assert r.total_interest == D("3471.23")  # 100000 * .07 * 181/365


def test_fd_broken_period_gets_simple_interest():
    # 1 quarter + 30 days: 100000*1.0175 = 101750, then 101750*.07*30/365 = 585.41
    r = fd_maturity(D("100000"), D("7"), date(2025, 1, 1), date(2025, 5, 1), CF.QUARTERLY, PT.CUMULATIVE)
    assert r.gross_maturity_value == D("102335.41")


def test_fd_monthly_payout():
    r = fd_maturity(D("100000"), D("7"), date(2025, 1, 1), date(2026, 1, 1), CF.QUARTERLY, PT.MONTHLY_PAYOUT)
    assert r.periodic_payout == D("583.33")
    assert r.payout_count == 12
    assert r.total_interest == D("7000.00")
    assert r.amount_at_maturity == D("100000.00")
    assert r.gross_maturity_value == D("107000.00")
    assert any("discounted" in a for a in r.assumptions)


def test_fd_quarterly_payout():
    r = fd_maturity(D("250000"), D("6.5"), date(2025, 1, 1), date(2027, 1, 1), CF.QUARTERLY, PT.QUARTERLY_PAYOUT)
    assert r.payout_count == 8
    assert r.periodic_payout == D("4062.50")
    assert r.total_interest == D("32500.00")


def test_fd_zero_rate():
    r = fd_maturity(D("5000"), D("0"), date(2025, 1, 1), date(2026, 1, 1), CF.QUARTERLY, PT.CUMULATIVE)
    assert r.total_interest == D("0.00")
    assert r.gross_maturity_value == D("5000.00")


def test_fd_tax_is_estimate_and_separate_from_gross():
    r = fd_maturity(D("100000"), D("7"), date(2025, 1, 1), date(2026, 1, 1), CF.QUARTERLY, PT.CUMULATIVE, D("30"))
    assert r.gross_maturity_value == D("107185.90")
    assert r.tax.estimated_tax == D("2155.77")
    assert r.tax.estimated_post_tax_value == D("105030.13")
    assert "Estimate" in r.tax.note


def test_fd_without_tax_slab_gives_no_tax_figures():
    r = fd_maturity(D("100000"), D("7"), date(2025, 1, 1), date(2026, 1, 1), CF.QUARTERLY, PT.CUMULATIVE)
    assert r.tax.estimated_tax is None and r.tax.estimated_post_tax_value is None


@pytest.mark.parametrize("kwargs", [
    {"principal": D("0")},
    {"rate": D("-1")},
    {"maturity": date(2024, 12, 31)},
])
def test_fd_rejects_invalid_input(kwargs):
    args = {"principal": D("1000"), "rate": D("7"), "maturity": date(2026, 1, 1)}
    args.update(kwargs)
    with pytest.raises(ValueError):
        fd_maturity(args["principal"], args["rate"], date(2025, 1, 1), args["maturity"], CF.QUARTERLY, PT.CUMULATIVE)


def test_fd_accrued_interest_to_date():
    start, mat = date(2025, 1, 1), date(2026, 1, 1)
    assert fd_accrued_interest(D("100000"), D("7"), start, mat, CF.QUARTERLY, PT.CUMULATIVE, date(2024, 6, 1)) == D("0.00")
    mid = fd_accrued_interest(D("100000"), D("7"), start, mat, CF.QUARTERLY, PT.CUMULATIVE, date(2025, 7, 1))
    assert mid == D("3530.63")  # two full quarters: 100000*(1.0175^2 - 1)
    # capped at maturity
    assert fd_accrued_interest(D("100000"), D("7"), start, mat, CF.QUARTERLY, PT.CUMULATIVE, date(2030, 1, 1)) == D("7185.90")


# ---------- RD ----------
def test_rd_matches_bank_formula_quarterly():
    # Bank formula: M = R[(1+i)^n - 1] / (1 - (1+i)^(-1/3)), i = 0.07/4, n = 4 quarters -> 12,462.13
    r = rd_maturity(D("1000"), D("7"), 12, CF.QUARTERLY)
    assert r.total_deposited == D("12000.00")
    assert r.gross_maturity_value == D("12462.13")
    assert r.total_interest == D("462.13")


def test_rd_simple_interest():
    # 1000 * .06 * (12+11+...+1)/12 = 1000 * .06 * 78/12 = 390
    r = rd_maturity(D("1000"), D("6"), 12, CF.SIMPLE)
    assert r.total_interest == D("390.00")


def test_rd_single_month():
    r = rd_maturity(D("1000"), D("12"), 1, CF.MONTHLY)
    assert r.gross_maturity_value == D("1010.00")


def test_rd_tax_estimate():
    r = rd_maturity(D("1000"), D("7"), 12, CF.QUARTERLY, D("20"))
    assert r.tax.estimated_tax == D("92.43")
    assert r.tax.estimated_post_tax_value == D("12369.70")


@pytest.mark.parametrize("inst,rate,months", [(D("0"), D("7"), 12), (D("100"), D("7"), 0), (D("100"), D("-2"), 12)])
def test_rd_rejects_invalid(inst, rate, months):
    with pytest.raises(ValueError):
        rd_maturity(inst, rate, months, CF.QUARTERLY)


def test_rd_progress():
    start = date(2025, 1, 1)
    assert rd_progress(D("1000"), D("7"), start, 12, CF.QUARTERLY, date(2024, 12, 1)) == (D("0"), D("0"))
    deposited, accrued = rd_progress(D("1000"), D("7"), start, 12, CF.QUARTERLY, date(2025, 6, 15))
    assert deposited == D("6000.00")  # Jan..Jun instalments
    assert D("0") < accrued < D("150")
    deposited, accrued = rd_progress(D("1000"), D("7"), start, 12, CF.QUARTERLY, date(2027, 1, 1))
    assert deposited == D("12000.00")
