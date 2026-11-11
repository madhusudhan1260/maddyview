"""Personal-finance records: bank accounts, income, expenses, ledger, liabilities, budgets."""

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import MONEY, RATE, Base, IdMixin, TimestampMixin, str_enum
from app.models.enums import AccountType, DataSource, LiabilityType, PaymentMethod, TxnDirection


def source_column(default: DataSource = DataSource.USER_ENTERED):
    return mapped_column(str_enum(DataSource, "data_source"), nullable=False, server_default=default.value, index=True)


def user_fk():
    return mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)


class BankAccount(IdMixin, TimestampMixin, Base):
    __tablename__ = "bank_accounts"
    __table_args__ = (CheckConstraint("last4 IS NULL OR last4 ~ '^[0-9]{4}$'", name="last4_digits"),)

    user_id: Mapped[int] = user_fk()
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    account_label: Mapped[str] = mapped_column(String(120), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(str_enum(AccountType, "account_type"), nullable=False)
    # Only the last 4 digits are ever stored — never a full account number.
    last4: Mapped[str | None] = mapped_column(String(4))
    balance: Mapped[Decimal] = mapped_column(MONEY, nullable=False, server_default="0")
    balance_as_of: Mapped[date | None] = mapped_column(Date)
    source: Mapped[DataSource] = source_column()


class IncomeRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "income_records"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_income_records_user_date", "user_id", "record_date"),
    )

    user_id: Mapped[int] = user_fk()
    bank_account_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("bank_accounts.id", ondelete="SET NULL"))
    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    income_source: Mapped[str] = mapped_column(String(120), nullable=False)  # e.g. employer, client
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[DataSource] = source_column()


class ExpenseRecord(IdMixin, TimestampMixin, Base):
    __tablename__ = "expense_records"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_expense_records_user_date", "user_id", "record_date"),
        Index("ix_expense_records_user_category", "user_id", "category"),
    )

    user_id: Mapped[int] = user_fk()
    bank_account_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("bank_accounts.id", ondelete="SET NULL"))
    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(str_enum(PaymentMethod, "payment_method"), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[DataSource] = source_column()


class Transaction(IdMixin, TimestampMixin, Base):
    """Bank-account ledger line (reserved for statement import in a later milestone)."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_transactions_account_date", "bank_account_id", "txn_date"),
    )

    user_id: Mapped[int] = user_fk()
    bank_account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False)
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    direction: Mapped[TxnDirection] = mapped_column(str_enum(TxnDirection, "txn_direction"), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(120))
    income_record_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("income_records.id", ondelete="SET NULL"))
    expense_record_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("expense_records.id", ondelete="SET NULL"))
    source: Mapped[DataSource] = source_column()


class Liability(IdMixin, TimestampMixin, Base):
    __tablename__ = "liabilities"
    __table_args__ = (
        CheckConstraint("outstanding_amount >= 0", name="outstanding_non_negative"),
        CheckConstraint("emi_amount IS NULL OR emi_amount >= 0", name="emi_non_negative"),
    )

    user_id: Mapped[int] = user_fk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    liability_type: Mapped[LiabilityType] = mapped_column(str_enum(LiabilityType, "liability_type"), nullable=False)
    lender: Mapped[str | None] = mapped_column(String(120))
    outstanding_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    interest_rate: Mapped[Decimal | None] = mapped_column(RATE)
    emi_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    source: Mapped[DataSource] = source_column()


class MonthlyBudget(IdMixin, TimestampMixin, Base):
    __tablename__ = "monthly_budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "month", "category"),
        CheckConstraint("budget_amount >= 0", name="budget_non_negative"),
        CheckConstraint("EXTRACT(DAY FROM month) = 1", name="month_first_day"),
    )

    user_id: Mapped[int] = user_fk()
    month: Mapped[date] = mapped_column(Date, nullable=False)  # first day of month
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    source: Mapped[DataSource] = source_column()
