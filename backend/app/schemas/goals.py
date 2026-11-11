from datetime import date
from decimal import Decimal
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from app.models.enums import GoalStatus
from app.schemas.common import DecimalOut, MoneyOut, Name, NonNegMoney, PatchModel, PositiveMoney, SourceLabelled

ReturnPercent = Annotated[Decimal, Field(ge=-50, le=50, max_digits=6, decimal_places=3)]
Notes = Annotated[str | None, Field(default=None, max_length=2000)]


class GoalProjectionOut(BaseModel):
    progress_percent: DecimalOut
    remaining_amount: MoneyOut
    months_to_goal: int | None
    estimated_completion_date: date | None
    required_monthly_contribution: MoneyOut | None
    on_track: bool | None
    projection_type: str
    assumption: str


class SavingsGoalCreate(BaseModel):
    name: Name
    target_amount: PositiveMoney
    current_amount: NonNegMoney = Decimal("0")
    target_date: date | None = None
    monthly_contribution: NonNegMoney = Decimal("0")
    notes: Notes = None
    status: GoalStatus = GoalStatus.ACTIVE


class SavingsGoalUpdate(PatchModel):
    nullable: ClassVar[set[str]] = {"target_date", "notes"}
    name: Name | None = None
    target_amount: PositiveMoney | None = None
    current_amount: NonNegMoney | None = None
    target_date: date | None = None
    monthly_contribution: NonNegMoney | None = None
    notes: Notes = None
    status: GoalStatus | None = None


class InvestmentGoalCreate(SavingsGoalCreate):
    expected_annual_return_percent: ReturnPercent
    risk_profile: Annotated[str | None, Field(default=None, max_length=30)]


class InvestmentGoalUpdate(SavingsGoalUpdate):
    nullable: ClassVar[set[str]] = {"target_date", "notes", "risk_profile"}
    expected_annual_return_percent: ReturnPercent | None = None
    risk_profile: Annotated[str | None, Field(default=None, max_length=30)]


class SavingsGoalOut(SourceLabelled):
    id: int
    name: str
    target_amount: MoneyOut
    current_amount: MoneyOut
    target_date: date | None
    monthly_contribution: MoneyOut
    notes: str | None
    status: GoalStatus
    projection: GoalProjectionOut


class InvestmentGoalOut(SavingsGoalOut):
    expected_annual_return_percent: DecimalOut
    risk_profile: str | None
