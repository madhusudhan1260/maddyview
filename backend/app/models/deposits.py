from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import MONEY, RATE, Base, IdMixin, TimestampMixin, str_enum
from app.models.enums import CompoundingFrequency, DataSource, DepositStatus, PayoutType
from app.models.finance import source_column, user_fk


class FixedDeposit(IdMixin, TimestampMixin, Base):
    __tablename__ = "fixed_deposits"
    __table_args__ = (
        CheckConstraint("principal > 0", name="principal_positive"),
        CheckConstraint("interest_rate >= 0 AND interest_rate <= 30", name="rate_range"),
        CheckConstraint("maturity_date > start_date", name="maturity_after_start"),
        Index("ix_fixed_deposits_user_maturity", "user_id", "maturity_date"),
    )

    user_id: Mapped[int] = user_fk()
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    principal: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(RATE, nullable=False)  # % p.a., entered by the user
    # False until the user confirms the rate against the bank's own document.
    rate_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    tenure_months: Mapped[int | None] = mapped_column(Integer)  # informational; dates are authoritative
    compounding_frequency: Mapped[CompoundingFrequency] = mapped_column(
        str_enum(CompoundingFrequency, "compounding_frequency"), nullable=False
    )
    payout_type: Mapped[PayoutType] = mapped_column(str_enum(PayoutType, "payout_type"), nullable=False)
    nominee_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DepositStatus] = mapped_column(
        str_enum(DepositStatus, "deposit_status"), nullable=False, server_default=DepositStatus.ACTIVE.value
    )
    source: Mapped[DataSource] = source_column()


class RecurringDeposit(IdMixin, TimestampMixin, Base):
    __tablename__ = "recurring_deposits"
    __table_args__ = (
        CheckConstraint("monthly_installment > 0", name="installment_positive"),
        CheckConstraint("interest_rate >= 0 AND interest_rate <= 30", name="rate_range"),
        CheckConstraint("tenure_months > 0", name="tenure_positive"),
        CheckConstraint("maturity_date > start_date", name="maturity_after_start"),
        Index("ix_recurring_deposits_user_maturity", "user_id", "maturity_date"),
    )

    user_id: Mapped[int] = user_fk()
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_installment: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(RATE, nullable=False)
    rate_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    compounding_frequency: Mapped[CompoundingFrequency] = mapped_column(
        str_enum(CompoundingFrequency, "compounding_frequency"), nullable=False
    )
    status: Mapped[DepositStatus] = mapped_column(
        str_enum(DepositStatus, "deposit_status"), nullable=False, server_default=DepositStatus.ACTIVE.value
    )
    source: Mapped[DataSource] = source_column()
