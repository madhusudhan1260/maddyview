from datetime import date
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, model_validator

from app.models.enums import CompoundingFrequency, DepositStatus, PayoutType
from app.schemas.common import DecimalOut, MoneyOut, Name, PatchModel, PositiveMoney, RatePercent, SourceLabelled

Tenure = Annotated[int, Field(ge=1, le=600)]


class TaxEstimateOut(BaseModel):
    slab_percent: DecimalOut | None
    estimated_tax: MoneyOut | None
    estimated_post_tax_interest: MoneyOut | None
    estimated_post_tax_value: MoneyOut | None
    note: str


# ---- FD ----
class _FDFields(BaseModel):
    @model_validator(mode="after")
    def _dates(self):
        s, m = getattr(self, "start_date", None), getattr(self, "maturity_date", None)
        if s and m and m <= s:
            raise ValueError("maturity_date must be after start_date")
        return self


class FDCalcIn(_FDFields):
    principal: PositiveMoney
    interest_rate: RatePercent
    start_date: date
    maturity_date: date
    compounding_frequency: CompoundingFrequency
    payout_type: PayoutType


class FDCreate(FDCalcIn):
    bank_name: Name
    tenure_months: Tenure | None = None
    rate_verified: bool = False
    nominee_notes: Annotated[str | None, Field(default=None, max_length=1000)]
    status: DepositStatus = DepositStatus.ACTIVE


class FDUpdate(PatchModel, _FDFields):
    nullable: ClassVar[set[str]] = {"tenure_months", "nominee_notes"}
    bank_name: Name | None = None
    principal: PositiveMoney | None = None
    interest_rate: RatePercent | None = None
    rate_verified: bool | None = None
    start_date: date | None = None
    maturity_date: date | None = None
    tenure_months: Tenure | None = None
    compounding_frequency: CompoundingFrequency | None = None
    payout_type: PayoutType | None = None
    nominee_notes: Annotated[str | None, Field(default=None, max_length=1000)]
    status: DepositStatus | None = None


class FDCalcOut(BaseModel):
    principal: MoneyOut
    tenure_days: int
    total_interest: MoneyOut
    gross_maturity_value: MoneyOut
    amount_at_maturity: MoneyOut
    periodic_payout: MoneyOut | None
    payout_count: int
    tax: TaxEstimateOut
    method: str
    assumptions: list[str]


class FDOut(SourceLabelled):
    id: int
    bank_name: str
    principal: MoneyOut
    interest_rate: DecimalOut
    rate_verified: bool
    start_date: date
    maturity_date: date
    tenure_months: int | None
    compounding_frequency: CompoundingFrequency
    payout_type: PayoutType
    nominee_notes: str | None
    status: DepositStatus
    calculation: FDCalcOut
    interest_earned_to_date: MoneyOut
    days_to_maturity: int


# ---- RD ----
class RDCalcIn(BaseModel):
    monthly_installment: PositiveMoney
    interest_rate: RatePercent
    tenure_months: Tenure
    compounding_frequency: CompoundingFrequency = CompoundingFrequency.QUARTERLY


class RDCreate(RDCalcIn):
    bank_name: Name
    start_date: date
    # Optional: derived as start_date + tenure_months when omitted; must match when given.
    maturity_date: date | None = None
    rate_verified: bool = False
    status: DepositStatus = DepositStatus.ACTIVE


class RDUpdate(PatchModel):
    bank_name: Name | None = None
    monthly_installment: PositiveMoney | None = None
    interest_rate: RatePercent | None = None
    rate_verified: bool | None = None
    start_date: date | None = None
    tenure_months: Tenure | None = None
    compounding_frequency: CompoundingFrequency | None = None
    status: DepositStatus | None = None


class RDCalcOut(BaseModel):
    monthly_installment: MoneyOut
    tenure_months: int
    total_deposited: MoneyOut
    total_interest: MoneyOut
    gross_maturity_value: MoneyOut
    tax: TaxEstimateOut
    method: str
    assumptions: list[str]


class RDOut(SourceLabelled):
    id: int
    bank_name: str
    monthly_installment: MoneyOut
    interest_rate: DecimalOut
    rate_verified: bool
    start_date: date
    maturity_date: date
    tenure_months: int
    compounding_frequency: CompoundingFrequency
    status: DepositStatus
    calculation: RDCalcOut
    deposited_to_date: MoneyOut
    interest_earned_to_date: MoneyOut
    days_to_maturity: int


class MaturityItem(SourceLabelled):
    id: int
    kind: str  # FD | RD
    bank_name: str
    maturity_date: date
    days_to_maturity: int
    gross_maturity_value: MoneyOut
    rate_verified: bool


class DepositSummary(BaseModel):
    active_fd_count: int
    active_rd_count: int
    fd_principal: MoneyOut
    rd_deposited_to_date: MoneyOut
    current_value: MoneyOut  # principal/deposits + interest accrued so far (gross)
    interest_earned_to_date: MoneyOut
    projected_maturity_value: MoneyOut
    projected_total_interest: MoneyOut
    estimated_tax_on_projected_interest: MoneyOut | None
    unverified_rate_count: int
    note: str
