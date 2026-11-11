"""DEMO dataset: illustrative, clearly-fictional records, every row labelled source=DEMO.

Bank names are fictional and every DEMO rate is marked unverified. Nothing here is real market data.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    BankAccount,
    ExpenseRecord,
    FixedDeposit,
    IncomeRecord,
    InvestmentGoal,
    Liability,
    RecurringDeposit,
    SavingsGoal,
    UserSettings,
)
from app.models.enums import (
    AccountType,
    CompoundingFrequency,
    DataSource,
    LiabilityType,
    PaymentMethod,
    PayoutType,
)
from app.services.calc.money import add_months, month_start

DEMO = DataSource.DEMO
DEMO_MODELS = [ExpenseRecord, IncomeRecord, FixedDeposit, RecurringDeposit, SavingsGoal, InvestmentGoal, Liability, BankAccount]


def has_demo(db: Session, user_id: int) -> bool:
    return any(
        db.scalar(select(m.id).where(m.user_id == user_id, m.source == DEMO).limit(1)) is not None for m in DEMO_MODELS
    )


def clear(db: Session, user_id: int) -> int:
    removed = 0
    for model in DEMO_MODELS:
        removed += db.execute(delete(model).where(model.user_id == user_id, model.source == DEMO)).rowcount or 0
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
    if settings:
        settings.include_demo_data = False
    return removed


def load(db: Session, user_id: int, today: date) -> int:
    clear(db, user_id)
    m0 = month_start(today)
    m1 = add_months(m0, -1)
    acct = BankAccount(user_id=user_id, bank_name="Demo Bank (fictional)", account_label="DEMO Savings",
                       account_type=AccountType.SAVINGS, last4="0000", balance=Decimal("85000.00"),
                       balance_as_of=today, source=DEMO)
    db.add(acct)
    db.flush()
    rows = [acct]
    for month in (m1, m0):
        rows += [
            IncomeRecord(user_id=user_id, bank_account_id=acct.id, amount=Decimal("75000.00"), income_source="DEMO Employer",
                         category="Salary", record_date=month, description="DEMO salary", source=DEMO),
            ExpenseRecord(user_id=user_id, amount=Decimal("18000.00"), category="Rent", record_date=month,
                          payment_method=PaymentMethod.NET_BANKING, description="DEMO rent", source=DEMO),
            ExpenseRecord(user_id=user_id, amount=Decimal("6500.00"), category="Groceries", record_date=month.replace(day=5),
                          payment_method=PaymentMethod.UPI, description="DEMO groceries", source=DEMO),
            ExpenseRecord(user_id=user_id, amount=Decimal("2400.50"), category="Utilities", record_date=month.replace(day=8),
                          payment_method=PaymentMethod.UPI, description="DEMO electricity + internet", source=DEMO),
        ]
    rows += [
        IncomeRecord(user_id=user_id, amount=Decimal("12000.00"), income_source="DEMO Freelance client", category="Freelance",
                     record_date=m0.replace(day=3), source=DEMO),
        ExpenseRecord(user_id=user_id, amount=Decimal("3200.00"), category="Dining", record_date=m0.replace(day=2),
                      payment_method=PaymentMethod.CREDIT_CARD, source=DEMO),
        FixedDeposit(user_id=user_id, bank_name="Demo Bank (fictional)", principal=Decimal("200000.00"),
                     interest_rate=Decimal("7.0000"), rate_verified=False, start_date=add_months(today, -11),
                     maturity_date=add_months(add_months(today, -11), 12), tenure_months=12,
                     compounding_frequency=CompoundingFrequency.QUARTERLY, payout_type=PayoutType.CUMULATIVE, source=DEMO),
        RecurringDeposit(user_id=user_id, bank_name="Demo Bank (fictional)", monthly_installment=Decimal("5000.00"),
                         interest_rate=Decimal("6.5000"), rate_verified=False, start_date=add_months(m0, -6),
                         maturity_date=add_months(add_months(m0, -6), 24), tenure_months=24,
                         compounding_frequency=CompoundingFrequency.QUARTERLY, source=DEMO),
        SavingsGoal(user_id=user_id, name="DEMO Emergency fund", target_amount=Decimal("300000.00"),
                    current_amount=Decimal("120000.00"), monthly_contribution=Decimal("15000.00"),
                    target_date=add_months(today, 12), source=DEMO),
        InvestmentGoal(user_id=user_id, name="DEMO Retirement corpus", target_amount=Decimal("5000000.00"),
                       current_amount=Decimal("250000.00"), monthly_contribution=Decimal("20000.00"),
                       expected_annual_return_percent=Decimal("10.000"), target_date=add_months(today, 240), source=DEMO),
        Liability(user_id=user_id, name="DEMO Car loan", liability_type=LiabilityType.CAR_LOAN, lender="Demo Bank (fictional)",
                  outstanding_amount=Decimal("340000.00"), interest_rate=Decimal("9.5000"), emi_amount=Decimal("11500.00"), source=DEMO),
    ]
    db.add_all(rows[1:])
    settings = db.scalar(select(UserSettings).where(UserSettings.user_id == user_id))
    if settings:
        settings.include_demo_data = True
    db.flush()
    return len(rows)
