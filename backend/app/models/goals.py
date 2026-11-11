from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import MONEY, Base, IdMixin, TimestampMixin, str_enum
from app.models.enums import DataSource, GoalStatus
from app.models.finance import source_column, user_fk


class _GoalColumns:
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False, server_default="0")
    target_date: Mapped[date | None] = mapped_column(Date)
    monthly_contribution: Mapped[Decimal] = mapped_column(MONEY, nullable=False, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[GoalStatus] = mapped_column(
        str_enum(GoalStatus, "goal_status"), nullable=False, server_default=GoalStatus.ACTIVE.value
    )


def _goal_checks():
    return (
        CheckConstraint("target_amount > 0", name="target_positive"),
        CheckConstraint("current_amount >= 0", name="current_non_negative"),
        CheckConstraint("monthly_contribution >= 0", name="contribution_non_negative"),
    )


class SavingsGoal(IdMixin, TimestampMixin, _GoalColumns, Base):
    """Cash savings — projections assume zero return (deterministic)."""

    __tablename__ = "savings_goals"
    __table_args__ = _goal_checks()

    user_id: Mapped[int] = user_fk()
    source: Mapped[DataSource] = source_column()


class InvestmentGoal(IdMixin, TimestampMixin, _GoalColumns, Base):
    """Market-linked goal — projections depend on an assumed, uncertain annual return."""

    __tablename__ = "investment_goals"
    __table_args__ = _goal_checks() + (
        CheckConstraint(
            "expected_annual_return_percent >= -50 AND expected_annual_return_percent <= 50", name="return_range"
        ),
    )

    user_id: Mapped[int] = user_fk()
    # User-supplied assumption, not a forecast.
    expected_annual_return_percent: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False, server_default="0")
    risk_profile: Mapped[str | None] = mapped_column(String(30))
    linked_portfolio_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("portfolios.id", ondelete="SET NULL"))
    source: Mapped[DataSource] = source_column()
