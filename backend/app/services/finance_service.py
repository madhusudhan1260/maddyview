"""Income, expense, bank-account and liability use-cases. Maths lives in services/calc."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import BankAccount, ExpenseRecord, IncomeRecord
from app.repositories import bank_account_repo, expense_repo, income_repo
from app.services.calc.money import add_months, month_start
from app.services.calc.personal_finance import MonthlySummary, monthly_summary


PAYMENT_LABELS = {
    "CASH": "Cash", "UPI": "UPI", "DEBIT_CARD": "Debit card", "CREDIT_CARD": "Credit card",
    "NET_BANKING": "Net banking", "CHEQUE": "Cheque", "OTHER": "Other",
}


def month_range(month: date) -> tuple[date, date]:
    start = month_start(month)
    return start, add_months(start, 1)


def ensure_account_owned(db: Session, user_id: int, bank_account_id: int | None) -> None:
    if bank_account_id is None:
        return
    owned = db.scalar(select(BankAccount.id).where(BankAccount.id == bank_account_id, BankAccount.user_id == user_id))
    if owned is None:
        raise AppError("bank_account_id does not refer to one of your accounts", code="invalid_reference", status_code=422)


def _filters(model, month: date | None, category: str | None):
    f = []
    if month:
        start, end = month_range(month)
        f += [model.record_date >= start, model.record_date < end]
    if category:
        f.append(model.category == category)
    return f


def list_income(db: Session, user_id: int, include_demo: bool, month: date | None = None, category: str | None = None):
    return income_repo.list(db, user_id, include_demo=include_demo, filters=_filters(IncomeRecord, month, category),
                            order_by=[IncomeRecord.record_date.desc(), IncomeRecord.id.desc()])


def list_expenses(db: Session, user_id: int, include_demo: bool, month: date | None = None, category: str | None = None):
    return expense_repo.list(db, user_id, include_demo=include_demo, filters=_filters(ExpenseRecord, month, category),
                             order_by=[ExpenseRecord.record_date.desc(), ExpenseRecord.id.desc()])


def summary_for_month(db: Session, user_id: int, include_demo: bool, month: date) -> MonthlySummary:
    incomes = list_income(db, user_id, include_demo, month)
    expenses = list_expenses(db, user_id, include_demo, month)
    return monthly_summary([i.amount for i in incomes], [(e.category, e.amount) for e in expenses])


def trend(db: Session, user_id: int, include_demo: bool, end_month: date, months: int) -> list[tuple[date, MonthlySummary]]:
    first = add_months(month_start(end_month), -(months - 1))
    return [(m, summary_for_month(db, user_id, include_demo, m)) for m in (add_months(first, i) for i in range(months))]


def transaction_history(db: Session, user_id: int, include_demo: bool, *, month: date | None = None,
                        category: str | None = None, kind: str | None = None, limit: int = 100) -> list[dict]:
    rows: list[dict] = []
    if kind in (None, "INCOME"):
        rows += [
            {"id": r.id, "kind": "INCOME", "amount": r.amount, "category": r.category, "record_date": r.record_date,
             "label": r.income_source, "description": r.description, "source": r.source, "_created": r.created_at}
            for r in list_income(db, user_id, include_demo, month, category)
        ]
    if kind in (None, "EXPENSE"):
        rows += [
            {"id": r.id, "kind": "EXPENSE", "amount": r.amount, "category": r.category, "record_date": r.record_date,
             "label": PAYMENT_LABELS[r.payment_method.value], "description": r.description,
             "source": r.source, "_created": r.created_at}
            for r in list_expenses(db, user_id, include_demo, month, category)
        ]
    rows.sort(key=lambda r: (r["record_date"], r["_created"]), reverse=True)
    return rows[:limit]


def categories(db: Session, user_id: int, model) -> list[str]:
    return list(db.scalars(select(model.category).where(model.user_id == user_id).distinct().order_by(model.category)))
