from sqlalchemy.orm import Session

from app.models import AuditLog


def record(db: Session, action: str, *, user_id: int | None, entity_type: str | None = None,
           entity_id: int | None = None, details: dict | None = None, ip: str | None = None) -> None:
    """Append an audit entry in the caller's transaction. Never put secrets or full amounts of credentials here."""
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details, ip_address=ip))
