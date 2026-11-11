from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import Ctx, CurrentCtx
from app.api.v1.crud import crud_router
from app.core import clock
from app.core.errors import AppError
from app.repositories import fd_repo, rd_repo
from app.schemas.deposits import (
    DepositSummary,
    FDCalcIn,
    FDCalcOut,
    FDCreate,
    FDOut,
    FDUpdate,
    MaturityItem,
    RDCalcIn,
    RDCalcOut,
    RDCreate,
    RDOut,
    RDUpdate,
)
from app.services import deposit_service
from app.services.calc.deposits import fd_maturity, rd_maturity

router = APIRouter()


def _validate_fd(ctx: Ctx, data: dict, obj) -> dict:
    start = data.get("start_date", obj.start_date if obj else None)
    maturity = data.get("maturity_date", obj.maturity_date if obj else None)
    if start and maturity and maturity <= start:
        raise AppError("maturity_date must be after start_date", code="validation_error", status_code=422)
    return data


def _validate_rd(ctx: Ctx, data: dict, obj) -> dict:
    start = data.get("start_date", obj.start_date if obj else None)
    tenure = data.get("tenure_months", obj.tenure_months if obj else None)
    given = data.get("maturity_date") if obj is None else None
    data["maturity_date"] = deposit_service.resolve_rd_maturity(start, tenure, given)
    return data


@router.post("/fixed-deposits/calculate", response_model=FDCalcOut, tags=["deposits"])
def calculate_fd(body: FDCalcIn, ctx: CurrentCtx):
    """Preview an FD calculation without saving anything."""
    return fd_maturity(body.principal, body.interest_rate, body.start_date, body.maturity_date,
                       body.compounding_frequency, body.payout_type, ctx.tax_slab)


@router.post("/recurring-deposits/calculate", response_model=RDCalcOut, tags=["deposits"])
def calculate_rd(body: RDCalcIn, ctx: CurrentCtx):
    """Preview an RD calculation without saving anything."""
    return rd_maturity(body.monthly_installment, body.interest_rate, body.tenure_months, body.compounding_frequency, ctx.tax_slab)


@router.get("/deposits/summary", response_model=DepositSummary, tags=["deposits"])
def deposits_summary(ctx: CurrentCtx):
    fds = fd_repo.list(ctx.db, ctx.user.id, include_demo=ctx.include_demo)
    rds = rd_repo.list(ctx.db, ctx.user.id, include_demo=ctx.include_demo)
    return deposit_service.summary(fds, rds, ctx.tax_slab, clock.today())


@router.get("/deposits/upcoming-maturities", response_model=list[MaturityItem], tags=["deposits"])
def upcoming(ctx: CurrentCtx, days: Annotated[int, Query(ge=1, le=3650)] = 90):
    fds = fd_repo.list(ctx.db, ctx.user.id, include_demo=ctx.include_demo)
    rds = rd_repo.list(ctx.db, ctx.user.id, include_demo=ctx.include_demo)
    return deposit_service.upcoming_maturities(fds, rds, clock.today(), days)


router.include_router(crud_router(
    path="/fixed-deposits", tag="deposits", repo=fd_repo, create_schema=FDCreate, update_schema=FDUpdate,
    out_schema=FDOut, entity="fixed_deposit", validate=_validate_fd,
    view=lambda ctx, fd: deposit_service.fd_view(fd, ctx.tax_slab, clock.today()),
    list_order=lambda m: [m.maturity_date, m.id],
))
router.include_router(crud_router(
    path="/recurring-deposits", tag="deposits", repo=rd_repo, create_schema=RDCreate, update_schema=RDUpdate,
    out_schema=RDOut, entity="recurring_deposit", validate=_validate_rd,
    view=lambda ctx, rd: deposit_service.rd_view(rd, ctx.tax_slab, clock.today()),
    list_order=lambda m: [m.maturity_date, m.id],
))
