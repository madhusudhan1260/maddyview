import re
from datetime import date
from decimal import Decimal
from typing import Annotated, ClassVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer, model_validator

from app.models.enums import DataSource


def _money_str(v: Decimal) -> str:
    return f"{v:.2f}"


# Monetary amounts travel as strings ("1234.50") so no precision is lost in JSON / JavaScript.
MoneyOut = Annotated[Decimal, PlainSerializer(_money_str, return_type=str, when_used="json")]
DecimalOut = Annotated[Decimal, PlainSerializer(lambda v: f"{v.normalize():f}", return_type=str, when_used="json")]

PositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=16, decimal_places=2)]
NonNegMoney = Annotated[Decimal, Field(ge=0, max_digits=16, decimal_places=2)]
RatePercent = Annotated[Decimal, Field(ge=0, le=30, max_digits=7, decimal_places=4)]


def _strip(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("must not be blank")
    return v


Name = Annotated[str, Field(min_length=1, max_length=120), AfterValidator(_strip)]
Category = Annotated[str, Field(min_length=1, max_length=60), AfterValidator(_strip)]
Description = Annotated[str | None, Field(default=None, max_length=2000)]

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def parse_month(value: str | None) -> date | None:
    """'2026-11' -> date(2026, 11, 1)."""
    if value is None:
        return None
    if not MONTH_RE.match(value):
        raise ValueError("month must be YYYY-MM")
    y, m = value.split("-")
    return date(int(y), int(m), 1)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SourceLabelled(ORMModel):
    source: DataSource


class Message(BaseModel):
    message: str


class PatchModel(BaseModel):
    """PATCH body: only sent fields are applied; explicit null is allowed only for nullable columns."""

    nullable: ClassVar[set[str]] = set()

    @model_validator(mode="after")
    def _no_null_for_required(self):
        bad = [f for f in self.model_fields_set if getattr(self, f) is None and f not in self.nullable]
        if bad:
            raise ValueError(f"these fields cannot be null: {', '.join(sorted(bad))}")
        return self

    def changes(self) -> dict:
        return self.model_dump(exclude_unset=True)
