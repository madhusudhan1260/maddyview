from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import Theme
from app.schemas.common import DecimalOut, ORMModel


class RegisterIn(BaseModel):
    email: EmailStr
    display_name: Annotated[str, Field(min_length=1, max_length=100)]
    password: Annotated[str, Field(min_length=12, max_length=128)]

    @field_validator("password")
    @classmethod
    def _strength(cls, v: str) -> str:
        classes = sum([any(c.islower() for c in v), any(c.isupper() for c in v), any(c.isdigit() for c in v), any(not c.isalnum() for c in v)])
        if classes < 3:
            raise ValueError("use at least 3 of: lowercase, uppercase, digit, symbol")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]


class UserOut(ORMModel):
    id: int
    email: str
    display_name: str
    last_login_at: datetime | None


class AuthStatus(BaseModel):
    setup_required: bool
    authenticated: bool
    user: UserOut | None = None


class SettingsOut(ORMModel):
    theme: Theme
    currency: str
    tax_slab_percent: DecimalOut | None
    include_demo_data: bool


class SettingsPatch(BaseModel):
    theme: Theme | None = None
    tax_slab_percent: Annotated[Decimal | None, Field(default=None, ge=0, le=50, max_digits=5, decimal_places=2)]
    include_demo_data: bool | None = None
