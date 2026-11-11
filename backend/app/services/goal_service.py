from datetime import date

from app.models import InvestmentGoal, SavingsGoal
from app.services.calc.goals import project_investment_goal, project_savings_goal

_COMMON = ("id", "name", "target_amount", "current_amount", "target_date", "monthly_contribution", "notes", "status", "source")


def savings_goal_view(g: SavingsGoal, today: date) -> dict:
    return {
        **{c: getattr(g, c) for c in _COMMON},
        "projection": project_savings_goal(g.target_amount, g.current_amount, g.monthly_contribution, today, g.target_date),
    }


def investment_goal_view(g: InvestmentGoal, today: date) -> dict:
    return {
        **{c: getattr(g, c) for c in _COMMON},
        "expected_annual_return_percent": g.expected_annual_return_percent,
        "risk_profile": g.risk_profile,
        "projection": project_investment_goal(g.target_amount, g.current_amount, g.monthly_contribution,
                                              g.expected_annual_return_percent, today, g.target_date),
    }
