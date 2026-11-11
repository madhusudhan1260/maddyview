"""Dashboard aggregation. Every figure is derived from the user's own records — nothing is invented."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Holding, Instrument, Portfolio
from app.models.enums import GoalStatus
from app.repositories import (
    bank_account_repo,
    fd_repo,
    investment_goal_repo,
    liability_repo,
    rd_repo,
    savings_goal_repo,
    visible_sources,
)
from app.services import deposit_service, finance_service
from app.services.calc.deposits import rd_progress
from app.services.calc.goals import progress_percent
from app.services.calc.money import HUNDRED, ZERO, round_money, round_pct

INSTRUMENT_LABELS = {"STOCK": "Stocks", "MUTUAL_FUND": "Mutual funds", "ETF": "ETFs", "BOND": "Bonds", "INDEX": "Index", "OTHER": "Other investments"}


def _holdings_at_cost(db: Session, user_id: int, include_demo: bool) -> dict[str, Decimal]:
    rows = db.execute(
        select(Instrument.instrument_type, Holding.quantity, Holding.avg_cost)
        .join(Portfolio, Holding.portfolio_id == Portfolio.id)
        .join(Instrument, Holding.instrument_id == Instrument.id)
        .where(Portfolio.user_id == user_id, Holding.source.in_(visible_sources(include_demo)))
    ).all()
    out: dict[str, Decimal] = {}
    for itype, qty, cost in rows:
        out[itype.value] = out.get(itype.value, ZERO) + qty * cost
    return {k: round_money(v) for k, v in out.items()}


def build(db: Session, user_id: int, include_demo: bool, tax_slab, today: date) -> dict:
    accounts = bank_account_repo.list(db, user_id, include_demo=include_demo)
    liabilities = liability_repo.list(db, user_id, include_demo=include_demo)
    fds = fd_repo.list(db, user_id, include_demo=include_demo)
    rds = rd_repo.list(db, user_id, include_demo=include_demo)
    s_goals = savings_goal_repo.list(db, user_id, include_demo=include_demo)
    i_goals = investment_goal_repo.list(db, user_id, include_demo=include_demo)

    bank_total = round_money(sum((a.balance for a in accounts), ZERO))
    active_fds = [f for f in fds if f.status in deposit_service.OPEN_STATUSES]
    active_rds = [r for r in rds if r.status in deposit_service.OPEN_STATUSES]
    fd_value = round_money(sum((deposit_service.fd_current_value(f, today) for f in active_fds), ZERO))
    rd_value = ZERO
    for r in active_rds:
        dep, acc = rd_progress(r.monthly_installment, r.interest_rate, r.start_date, r.tenure_months, r.compounding_frequency, today)
        rd_value += dep + acc
    rd_value = round_money(rd_value)
    holdings = _holdings_at_cost(db, user_id, include_demo)
    investments_at_cost = round_money(sum(holdings.values(), ZERO))

    total_assets = round_money(bank_total + fd_value + rd_value + investments_at_cost)
    total_liabilities = round_money(sum((l.outstanding_amount for l in liabilities), ZERO))

    allocation_raw = [("Bank balances", bank_total), ("Fixed deposits", fd_value), ("Recurring deposits", rd_value)]
    allocation_raw += [(INSTRUMENT_LABELS.get(k, k), v) for k, v in sorted(holdings.items())]
    allocation = [
        {"asset_class": name, "amount": amt, "percent": round_pct(amt / total_assets * HUNDRED)}
        for name, amt in allocation_raw if amt > 0
    ] if total_assets > 0 else []

    month = finance_service.summary_for_month(db, user_id, include_demo, today)

    goals = []
    for g, kind in [*((g, "SAVINGS") for g in s_goals), *((g, "INVESTMENT") for g in i_goals)]:
        if g.status in (GoalStatus.ACTIVE, GoalStatus.ACHIEVED):
            goals.append({"id": g.id, "kind": kind, "name": g.name, "target_amount": g.target_amount,
                          "current_amount": g.current_amount, "target_date": g.target_date,
                          "progress_percent": progress_percent(g.current_amount, g.target_amount), "source": g.source})
    goal_target = sum((g["target_amount"] for g in goals), ZERO)
    goal_current = sum((min(g["current_amount"], g["target_amount"]) for g in goals), ZERO)

    recent = finance_service.transaction_history(db, user_id, include_demo, limit=8)
    for r in recent:
        r.pop("_created", None)

    return {
        "as_of": today,
        "includes_demo": include_demo,
        "net_worth": {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_worth": round_money(total_assets - total_liabilities),
            "bank_balances": bank_total,
            "fixed_deposits": fd_value,
            "recurring_deposits": rd_value,
            "investments_at_cost": investments_at_cost,
        },
        "investments": {
            "total_at_cost": investments_at_cost,
            "holding_count": sum(1 for _ in holdings),
            "valuation_note": "Valued at purchase cost. Live market prices are not connected yet.",
        },
        "month": {
            "month": today.strftime("%Y-%m"),
            "income": month.total_income,
            "expenses": month.total_expenses,
            "savings": month.savings,
            "savings_rate": month.savings_rate,
        },
        "goals": {
            "count": len(goals),
            "overall_progress_percent": round_pct(goal_current / goal_target * HUNDRED) if goal_target > 0 else None,
            "items": goals[:6],
        },
        "allocation": allocation,
        "recent_transactions": recent,
        "upcoming_maturities": deposit_service.upcoming_maturities(fds, rds, today, 90)[:6],
        "ai_reports": [],
        "ai_reports_note": "AI research reports arrive in a later milestone. None have been generated.",
        "counts": {
            "bank_accounts": len(accounts),
            "liabilities": len(liabilities),
            "fixed_deposits": len(fds),
            "recurring_deposits": len(rds),
            "goals": len(s_goals) + len(i_goals),
            "transactions": len(recent),
        },
    }
