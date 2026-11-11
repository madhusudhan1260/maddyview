from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import get_settings
from app.core.errors import AuthError, ConflictError
from app.core.security import hash_password, hash_token, needs_rehash, new_session_token, verify_password
from app.models import AuthSession, User, UserSettings
from app.services import audit

# Verifying against a dummy hash keeps response time similar for unknown emails.
_DUMMY_HASH = hash_password("dummy-password-for-timing-equalisation")


def user_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User)) or 0


def register_first_user(db: Session, email: str, display_name: str, password: str, ip: str | None) -> User:
    """MaddyView is single-user: registration is only open while no account exists."""
    if user_count(db) > 0:
        raise ConflictError("An account already exists. Sign in instead.", code="setup_complete")
    user = User(email=email.lower(), display_name=display_name.strip(), password_hash=hash_password(password))
    user.settings = UserSettings()
    db.add(user)
    db.flush()
    audit.record(db, "auth.register", user_id=user.id, entity_type="user", entity_id=user.id, ip=ip)
    return user


def authenticate(db: Session, email: str, password: str, ip: str | None) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not user.is_active:
        verify_password(_DUMMY_HASH, password)
        audit.record(db, "auth.login_failed", user_id=None, details={"reason": "unknown_user"}, ip=ip)
        db.commit()
        raise AuthError("Invalid email or password")
    if not verify_password(user.password_hash, password):
        audit.record(db, "auth.login_failed", user_id=user.id, details={"reason": "bad_password"}, ip=ip)
        db.commit()
        raise AuthError("Invalid email or password")
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.last_login_at = clock.now_utc()
    return user


def create_session(db: Session, user: User, ip: str | None, user_agent: str | None) -> str:
    token = new_session_token()
    db.add(AuthSession(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=clock.now_utc() + timedelta(hours=get_settings().session_ttl_hours),
        ip_address=ip,
        user_agent=(user_agent or "")[:255] or None,
    ))
    audit.record(db, "auth.login", user_id=user.id, ip=ip)
    return token


def resolve_session(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    sess = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(token)))
    if sess is None or sess.revoked_at is not None or sess.expires_at <= clock.now_utc():
        return None
    user = sess.user
    return user if user.is_active else None


def revoke_session(db: Session, token: str | None, ip: str | None) -> None:
    if not token:
        return
    sess = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(token)))
    if sess and sess.revoked_at is None:
        sess.revoked_at = clock.now_utc()
        audit.record(db, "auth.logout", user_id=sess.user_id, ip=ip)


def revoke_all_sessions(db: Session, user_id: int) -> None:
    db.execute(update(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)).values(revoked_at=clock.now_utc()))
