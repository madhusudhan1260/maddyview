from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select, text

from app.api.deps import DB, CurrentCtx
from app.core import clock
from app.core.config import get_settings
from app.models import AuditLog
from app.models.enums import DataSource
from app.schemas.common import Message
from app.services import audit, dashboard_service, demo_service

router = APIRouter()


class HealthOut(BaseModel):
    status: str
    version: str
    database: str
    time: datetime


@router.get("/health", response_model=HealthOut, tags=["system"])
def health(db: DB):
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001 — health must report, not raise
        database = "unavailable"
    return HealthOut(status="ok" if database == "ok" else "degraded", version="0.1.0", database=database, time=clock.now_utc())


@router.get("/dashboard", tags=["dashboard"])
def dashboard(ctx: CurrentCtx):
    """Aggregated dashboard. Money values are strings with two decimals."""
    data = dashboard_service.build(ctx.db, ctx.user.id, ctx.include_demo, ctx.tax_slab, clock.today())
    return _jsonable(data)


def _jsonable(v):
    from decimal import Decimal
    from enum import Enum
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_jsonable(x) for x in v]
    if isinstance(v, Decimal):
        return f"{v:.2f}"
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


class DataSourceInfo(BaseModel):
    label: DataSource
    meaning: str


_SOURCE_MEANINGS = {
    DataSource.REAL: "Verified from an authoritative external provider.",
    DataSource.DEMO: "Illustrative sample data. Not your money and not real market data.",
    DataSource.USER_ENTERED: "Entered by you manually. Accuracy depends on your input.",
    DataSource.SIMULATED: "Output of paper trading or a simulation. No real money involved.",
    DataSource.AI_DERIVED: "Produced by a model. Uncertain by nature; not financial advice.",
}


@router.get("/data-sources/labels", response_model=list[DataSourceInfo], tags=["system"])
def data_source_labels():
    return [DataSourceInfo(label=k, meaning=v) for k, v in _SOURCE_MEANINGS.items()]


class DemoStatus(BaseModel):
    has_demo_data: bool
    include_demo_data: bool


@router.get("/demo", response_model=DemoStatus, tags=["demo"])
def demo_status(ctx: CurrentCtx):
    return DemoStatus(has_demo_data=demo_service.has_demo(ctx.db, ctx.user.id), include_demo_data=ctx.include_demo)


@router.post("/demo", response_model=Message, tags=["demo"])
def load_demo(ctx: CurrentCtx):
    n = demo_service.load(ctx.db, ctx.user.id, clock.today())
    audit.record(ctx.db, "demo.load", user_id=ctx.user.id, details={"rows": n}, ip=ctx.ip)
    ctx.db.commit()
    return Message(message=f"Loaded {n} DEMO records. They are labelled DEMO everywhere.")


@router.delete("/demo", response_model=Message, tags=["demo"])
def clear_demo(ctx: CurrentCtx):
    n = demo_service.clear(ctx.db, ctx.user.id)
    audit.record(ctx.db, "demo.clear", user_id=ctx.user.id, details={"rows": n}, ip=ctx.ip)
    ctx.db.commit()
    return Message(message=f"Removed {n} DEMO records.")


class AuditOut(BaseModel):
    id: int
    action: str
    entity_type: str | None
    entity_id: int | None
    details: dict | None
    ip_address: str | None
    created_at: datetime


@router.get("/audit-logs", response_model=list[AuditOut], tags=["system"])
def audit_logs(ctx: CurrentCtx, limit: Annotated[int, Query(ge=1, le=200)] = 50):
    rows = ctx.db.scalars(select(AuditLog).where(AuditLog.user_id == ctx.user.id).order_by(AuditLog.id.desc()).limit(limit))
    return [AuditOut.model_validate(r, from_attributes=True) for r in rows]


@router.get("/meta", tags=["system"])
def meta():
    s = get_settings()
    return {"app": s.app_name, "env": s.env, "api_version": "v1"}
