from datetime import date, datetime
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, Field

from app.models.enums import AccountType, LiabilityType, PaymentMethod
from app.schemas.common import (
    Category,
    DecimalOut,
    Description,
    MoneyOut,
    Name,
    NonNegMoney,
    PositiveMoney,
    RatePercent,
    PatchModel,
    SourceLabelled,
)


# ---- income ----
class IncomeCreate(BaseModel):
    amount: PositiveMoney
    income_source: Name
    category: Category
    record_date: date
    description: Description = None
    bank_account_id: int | None = None


class IncomeUpdate(PatchModel):
    nullable: ClassVar[set[str]] = {"description", "bank_account_id"}
    amount: PositiveMoney | None = None
    income_source: Name | None = None
    category: Category | None = None
    record_date: date | None = None
    description: Description = None
    bank_account_id: int | None = None


class IncomeOut(SourceLabelled):
    id: int
    amount: MoneyOut
    income_source: str
    category: str
    record_date: date
    description: str | None
    bank_account_id: int | None
    created_at: datetime
    updated_at: datetime


# ---- expenses ----
class ExpenseCreate(BaseModel):
    amount: PositiveMoney
    category: Category
    record_date: date
    payment_method: PaymentMethod
    description: Description = None
    bank_account_id: int | None = None


class ExpenseUpdate(PatchModel):
    nullable: ClassVar[set[str]] = {"description", "bank_account_id"}
    amount: PositiveMoney | None = None
    category: Category | None = None
    record_date: date | None = None
    payment_method: PaymentMethod | None = None
    description: Description = None
    bank_account_id: int | None = None


class ExpenseOut(SourceLabelled):
    id: int
    amount: MoneyOut
    category: str
    record_date: date
    payment_method: PaymentMethod
    description: str | None
    bank_account_id: int | None
    created_at: datetime
    updated_at: datetime


# ---- summaries ----
class CategoryShareOut(BaseModel):
    category: str
    amount: MoneyOut
    percent: DecimalOut


class MonthlySummaryOut(BaseModel):
    month: str
    total_income: MoneyOut
    total_expenses: MoneyOut
    savings: MoneyOut
    savings_rate: DecimalOut | None
    savings_rate_note: str | None
    income_count: int
    expense_count: int
    expense_breakdown: list[CategoryShareOut]


class TrendPoint(BaseModel):
    month: str
    income: MoneyOut
    expenses: MoneyOut
    savings: MoneyOut


class TransactionRow(SourceLabelled):
    id: int
    kind: Literal["INCOME", "EXPENSE"]
    amount: MoneyOut
    category: str
    record_date: date
    label: str  # income source or payment method
    description: str | None


# ---- bank accounts ----
class BankAccountCreate(BaseModel):
    bank_name: Name
    account_label: Name
    account_type: AccountType
    last4: Annotated[str | None, Field(default=None, pattern=r"^\d{4}$")]
    balance: NonNegMoney
    balance_as_of: date | None = None


class BankAccountUpdate(PatchModel):
    nullable: ClassVar[set[str]] = {"last4", "balance_as_of"}
    bank_name: Name | None = None
    account_label: Name | None = None
    account_type: AccountType | None = None
    last4: Annotated[str | None, Field(default=None, pattern=r"^\d{4}$")]
    balance: NonNegMoney | None = None
    balance_as_of: date | None = None


class BankAccountOut(SourceLabelled):
    id: int
    bank_name: str
    account_label: str
    account_type: AccountType
    last4: str | None
    balance: MoneyOut
    balance_as_of: date | None


# ---- liabilities ----
class LiabilityCreate(BaseModel):
    name: Name
    liability_type: LiabilityType
    lender: Annotated[str | None, Field(default=None, max_length=120)]
    outstanding_amount: NonNegMoney
    interest_rate: RatePercent | None = None
    emi_amount: NonNegMoney | None = None


class LiabilityUpdate(PatchModel):
    nullable: ClassVar[set[str]] = {"lender", "interest_rate", "emi_amount"}
    name: Name | None = None
    liability_type: LiabilityType | None = None
    lender: Annotated[str | None, Field(default=None, max_length=120)]
    outstanding_amount: NonNegMoney | None = None
    interest_rate: RatePercent | None = None
    emi_amount: NonNegMoney | None = None


class LiabilityOut(SourceLabelled):
    id: int
    name: str
    liability_type: LiabilityType
    lender: str | None
    outstanding_amount: MoneyOut
    interest_rate: DecimalOut | None
    emi_amount: MoneyOut | None
