from datetime import date
from decimal import Decimal as D

import pytest

from app.services.calc.goals import (
    future_value,
    monthly_rate_from_annual,
    progress_percent,
    project_investment_goal,
    project_savings_goal,
)

TODAY = date(2026, 1, 15)


def test_progress_percent_capped_and_rounded():
    assert progress_percent(D("1"), D("3")) == D("33.33")
    assert progress_percent(D("500"), D("100")) == D("100.00")
    assert progress_percent(D("0"), D("100")) == D("0.00")
    with pytest.raises(ValueError):
        progress_percent(D("1"), D("0"))


def test_savings_goal_projection():
    p = project_savings_goal(D("100000"), D("20000"), D("5000"), TODAY, date(2027, 1, 15))
    assert p.progress_percent == D("20.00")
    assert p.remaining_amount == D("80000.00")
    assert p.months_to_goal == 16
    assert p.estimated_completion_date == date(2027, 5, 15)
    assert p.required_monthly_contribution == D("6666.67")
    assert p.on_track is False
    assert p.projection_type == "DETERMINISTIC"


def test_savings_goal_rounds_partial_month_up():
    p = project_savings_goal(D("1000"), D("0"), D("300"), TODAY)
    assert p.months_to_goal == 4
    assert p.on_track is None and p.required_monthly_contribution is None


def test_savings_goal_without_contribution_is_unreachable():
    p = project_savings_goal(D("1000"), D("10"), D("0"), TODAY)
    assert p.months_to_goal is None and p.estimated_completion_date is None


def test_achieved_goal():
    p = project_savings_goal(D("1000"), D("1200"), D("0"), TODAY, date(2026, 6, 1))
    assert p.months_to_goal == 0
    assert p.estimated_completion_date == TODAY
    assert p.remaining_amount == D("0.00")
    assert p.on_track is True


def test_target_date_in_past():
    p = project_savings_goal(D("1000"), D("400"), D("100"), TODAY, date(2025, 1, 1))
    assert p.required_monthly_contribution == D("600.00")
    assert p.on_track is False


def test_monthly_rate_from_annual():
    m = monthly_rate_from_annual(D("12"))
    assert abs((1 + m) ** 12 - D("1.12")) < D("1e-20")
    assert monthly_rate_from_annual(D("0")) == 0
    with pytest.raises(ValueError):
        monthly_rate_from_annual(D("-100"))


def test_investment_goal_projection_with_assumed_return():
    p = project_investment_goal(D("1000000"), D("100000"), D("10000"), D("12"), TODAY, date(2031, 1, 15))
    assert p.projection_type == "ASSUMED_RETURN"
    assert "not guaranteed" in p.assumption
    assert p.months_to_goal == 62
    # the required contribution should land exactly on target after 60 months
    m = monthly_rate_from_annual(D("12"))
    fv = future_value(D("100000"), p.required_monthly_contribution, m, 60)
    assert abs(fv - D("1000000")) < D("1")


def test_investment_goal_zero_return_equals_savings_maths():
    a = project_investment_goal(D("12000"), D("0"), D("1000"), D("0"), TODAY, date(2027, 1, 15))
    b = project_savings_goal(D("12000"), D("0"), D("1000"), TODAY, date(2027, 1, 15))
    assert a.months_to_goal == b.months_to_goal == 12
    assert a.required_monthly_contribution == b.required_monthly_contribution == D("1000.00")


def test_investment_goal_negative_return_can_be_unreachable():
    p = project_investment_goal(D("1000000"), D("1000"), D("10"), D("-10"), TODAY)
    assert p.months_to_goal is None


def test_investment_goal_growth_alone_reaches_target():
    p = project_investment_goal(D("1100"), D("1000"), D("0"), D("10"), TODAY)
    assert p.months_to_goal == 12
