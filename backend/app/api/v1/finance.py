from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.api.deps import Ctx, CurrentCtx
from app.api.v1.crud import crud_router
from app.core import clock
from app.core.errors import AppError
from app.models import ExpenseRecord, IncomeRecord
from app.repositories import bank_account_repo, expense_repo, income_repo, liability_repo
from app.schemas.common import parse_month
from app.schemas.finance import (
    BankAccountCreate,
    BankAccountOut,
    BankAccountUpdate,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    IncomeCreate,
    IncomeOut,
    IncomeUpdate,
    LiabilityCreate,
    LiabilityOut,
    LiabilityUpdate,
    MonthlySummaryOut,
    TransactionRow,
    TrendPoint,
)
from app.services import finance_service

MonthQ = Annotated[str | None, Query(description="YYYY-MM", examples=["2026-11"])]
CategoryQ = Annotated[str | None, Query(max_length=60)]


def _month(value: str | None):
    try:
        return parse_month(value)
    except ValueError as exc:
        raise AppError(str(exc), code="validation_error", status_code=422) from exc


def _check_account(ctx: Ctx, data: dict, obj) -> dict:
    finance_service.ensure_account_owned(ctx.db, ctx.user.id, data.get("bank_account_id"))
    return data


router = APIRouter()

# Explicit filtered list endpoints for income/expenses (registered before the CRUD routers).
@router.get("/income", response_model=list[IncomeOut], tags=["personal-finance"])
def list_income(ctx: CurrentCtx, month: MonthQ = None, category: CategoryQ = None):
    return finance_service.list_income(ctx.db, ctx.user.id, ctx.include_demo, _month(month), category)


@router.get("/expenses", response_model=list[ExpenseOut], tags=["personal-finance"])
def list_expenses(ctx: CurrentCtx, month: MonthQ = None, category: CategoryQ = None):
    return finance_service.list_expenses(ctx.db, ctx.user.id, ctx.include_demo, _month(month), category)


@router.get("/income-categories", response_model=list[str], tags=["personal-finance"])
def income_categories(ctx: CurrentCtx):
    return finance_service.categories(ctx.db, ctx.user.id, IncomeRecord)


@router.get("/expense-categories", response_model=list[str], tags=["personal-finance"])
def expense_categories(ctx: CurrentCtx):
    return finance_service.categories(ctx.db, ctx.user.id, ExpenseRecord)


@router.get("/finance/summary", response_model=MonthlySummaryOut, tags=["personal-finance"])
def monthly_summary(ctx: CurrentCtx, month: MonthQ = None):
    m = _month(month) or clock.today().replace(day=1)
    s = finance_service.summary_for_month(ctx.db, ctx.user.id, ctx.include_demo, m)
    return {
        "month": m.strftime("%Y-%m"),
        **s.__dict__,
        "expense_breakdown": [c.__dict__ for c in s.expense_breakdown],
        "savings_rate_note": None if s.savings_rate is not None else "No income recorded for this month, so a savings rate cannot be calculated.",
    }


@router.get("/finance/trend", response_model=list[TrendPoint], tags=["personal-finance"])
def monthly_trend(ctx: CurrentCtx, months: Annotated[int, Query(ge=1, le=36)] = 6):
    return [
        {"month": m.strftime("%Y-%m"), "income": s.total_income, "expenses": s.total_expenses, "savings": s.savings}
        for m, s in finance_service.trend(ctx.db, ctx.user.id, ctx.include_demo, clock.today(), months)
    ]


@router.get("/finance/transactions", response_model=list[TransactionRow], tags=["personal-finance"])
def transactions(
    ctx: CurrentCtx,
    month: MonthQ = None,
    category: CategoryQ = None,
    kind: Literal["INCOME", "EXPENSE"] | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    return finance_service.transaction_history(ctx.db, ctx.user.id, ctx.include_demo, month=_month(month),
                                               category=category, kind=kind, limit=limit)


router.include_router(crud_router(path="/income", tag="personal-finance", repo=income_repo, create_schema=IncomeCreate,
                                  update_schema=IncomeUpdate, out_schema=IncomeOut, entity="income",
                                  validate=_check_account, include_list=False))
router.include_router(crud_router(path="/expenses", tag="personal-finance", repo=expense_repo, create_schema=ExpenseCreate,
                                  update_schema=ExpenseUpdate, out_schema=ExpenseOut, entity="expense",
                                  validate=_check_account, include_list=False))
router.include_router(crud_router(path="/bank-accounts", tag="accounts", repo=bank_account_repo, create_schema=BankAccountCreate,
                                  update_schema=BankAccountUpdate, out_schema=BankAccountOut, entity="bank_account",
                                  list_order=lambda m: [m.bank_name, m.id]))
router.include_router(crud_router(path="/liabilities", tag="accounts", repo=liability_repo, create_schema=LiabilityCreate,
                                  update_schema=LiabilityUpdate, out_schema=LiabilityOut, entity="liability",
                                  list_order=lambda m: [m.outstanding_amount.desc(), m.id]))
