from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import DB, CurrentCtx, client_ip
from app.core.config import get_settings
from app.core.rate_limit import limit_auth
from app.schemas.auth import AuthStatus, LoginIn, RegisterIn, SettingsOut, SettingsPatch, UserOut
from app.schemas.common import Message
from app.services import audit, auth_service

router = APIRouter(tags=["auth"])


def _set_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        s.session_cookie_name, token, max_age=s.session_ttl_hours * 3600,
        httponly=True, secure=s.cookie_secure, samesite="lax", path="/api",
    )


@router.get("/auth/status", response_model=AuthStatus)
def auth_status(request: Request, db: DB):
    user = auth_service.resolve_session(db, request.cookies.get(get_settings().session_cookie_name))
    return AuthStatus(setup_required=auth_service.user_count(db) == 0, authenticated=user is not None,
                      user=UserOut.model_validate(user) if user else None)


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(limit_auth)])
def register(body: RegisterIn, request: Request, response: Response, db: DB):
    user = auth_service.register_first_user(db, body.email, body.display_name, body.password, client_ip(request))
    token = auth_service.create_session(db, user, client_ip(request), request.headers.get("user-agent"))
    db.commit()
    _set_cookie(response, token)
    return user


@router.post("/auth/login", response_model=UserOut, dependencies=[Depends(limit_auth)])
def login(body: LoginIn, request: Request, response: Response, db: DB):
    user = auth_service.authenticate(db, body.email, body.password, client_ip(request))
    token = auth_service.create_session(db, user, client_ip(request), request.headers.get("user-agent"))
    db.commit()
    _set_cookie(response, token)
    return user


@router.post("/auth/logout", response_model=Message)
def logout(request: Request, response: Response, db: DB):
    s = get_settings()
    auth_service.revoke_session(db, request.cookies.get(s.session_cookie_name), client_ip(request))
    db.commit()
    response.delete_cookie(s.session_cookie_name, path="/api")
    return Message(message="Signed out")


@router.get("/auth/me", response_model=UserOut)
def me(ctx: CurrentCtx):
    return ctx.user


@router.get("/settings", response_model=SettingsOut)
def get_settings_route(ctx: CurrentCtx):
    return ctx.settings


@router.patch("/settings", response_model=SettingsOut)
def patch_settings(body: SettingsPatch, ctx: CurrentCtx):
    # Sending tax_slab_percent: null clears the slab; other fields ignore null.
    changes = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None or k == "tax_slab_percent"}
    for k, v in changes.items():
        setattr(ctx.settings, k, v)
    audit.record(ctx.db, "settings.update", user_id=ctx.user.id, entity_type="user_settings",
                 entity_id=ctx.settings.id, details={"fields": sorted(changes)}, ip=ctx.ip)
    ctx.db.commit()
    return ctx.settings
