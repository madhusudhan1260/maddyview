from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthError
from app.database.session import get_db
from app.models import User, UserSettings
from app.services import auth_service

DB = Annotated[Session, Depends(get_db)]


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@dataclass
class Ctx:
    db: Session
    user: User
    settings: UserSettings
    ip: str | None

    @property
    def include_demo(self) -> bool:
        return bool(self.settings.include_demo_data)

    @property
    def tax_slab(self):
        return self.settings.tax_slab_percent


def current_ctx(request: Request, db: DB) -> Ctx:
    token = request.cookies.get(get_settings().session_cookie_name)
    user = auth_service.resolve_session(db, token)
    if user is None:
        raise AuthError("Sign in required")
    if user.settings is None:  # defensive: settings row is created at registration
        user.settings = UserSettings()
        db.commit()
    return Ctx(db=db, user=user, settings=user.settings, ip=client_ip(request))


CurrentCtx = Annotated[Ctx, Depends(current_ctx)]
