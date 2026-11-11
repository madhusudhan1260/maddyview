"""FD/RD use-cases: enrich stored deposits with calculation results and aggregate them."""

from datetime import date
from decimal import Decimal

from app.core.errors import AppError
from app.models import FixedDeposit, RecurringDeposit
from app.models.enums import DepositStatus, PayoutType
from app.services.calc.deposits import (
    FDResult,
    RDResult,
    estimate_tax,
    fd_accrued_interest,
    fd_maturity,
    rd_maturity,
    rd_progress,
)
from app.services.calc.money import ZERO, add_months, round_money

OPEN_STATUSES = (DepositStatus.ACTIVE,)


def fd_calc(fd: FixedDeposit, tax_slab) -> FDResult:
    return fd_maturity(fd.principal, fd.interest_rate, fd.start_date, fd.maturity_date,
                       fd.compounding_frequency, fd.payout_type, tax_slab)


def rd_calc(rd: RecurringDeposit, tax_slab) -> RDResult:
    return rd_maturity(rd.monthly_installment, rd.interest_rate, rd.tenure_months, rd.compounding_frequency, tax_slab)


def fd_view(fd: FixedDeposit, tax_slab, today: date) -> dict:
    return {
        **{c: getattr(fd, c) for c in (
            "id", "bank_name", "principal", "interest_rate", "rate_verified", "start_date", "maturity_date",
            "tenure_months", "compounding_frequency", "payout_type", "nominee_notes", "status", "source")},
        "calculation": fd_calc(fd, tax_slab),
        "interest_earned_to_date": fd_accrued_interest(fd.principal, fd.interest_rate, fd.start_date, fd.maturity_date,
                                                       fd.compounding_frequency, fd.payout_type, today),
        "days_to_maturity": (fd.maturity_date - today).days,
    }


def rd_view(rd: RecurringDeposit, tax_slab, today: date) -> dict:
    deposited, accrued = rd_progress(rd.monthly_installment, rd.interest_rate, rd.start_date, rd.tenure_months,
                                     rd.compounding_frequency, today)
    return {
        **{c: getattr(rd, c) for c in (
            "id", "bank_name", "monthly_installment", "interest_rate", "rate_verified", "start_date", "maturity_date",
            "tenure_months", "compounding_frequency", "status", "source")},
        "calculation": rd_calc(rd, tax_slab),
        "deposited_to_date": deposited,
        "interest_earned_to_date": accrued,
        "days_to_maturity": (rd.maturity_date - today).days,
    }


def resolve_rd_maturity(start: date, tenure_months: int, given: date | None) -> date:
    derived = add_months(start, tenure_months)
    if given is not None and given != derived:
        raise AppError(
            f"maturity_date must equal start_date + tenure_months ({derived.isoformat()})",
            code="validation_error", status_code=422,
        )
    return derived


def fd_current_value(fd: FixedDeposit, today: date) -> Decimal:
    """Principal plus interest that has accrued but not been paid out (cumulative deposits only)."""
    if fd.payout_type != PayoutType.CUMULATIVE:
        return fd.principal
    return round_money(fd.principal + fd_accrued_interest(fd.principal, fd.interest_rate, fd.start_date, fd.maturity_date,
                                                          fd.compounding_frequency, fd.payout_type, today))


def summary(fds: list[FixedDeposit], rds: list[RecurringDeposit], tax_slab, today: date) -> dict:
    active_fds = [f for f in fds if f.status in OPEN_STATUSES]
    active_rds = [r for r in rds if r.status in OPEN_STATUSES]
    fd_principal = sum((f.principal for f in active_fds), ZERO)
    current = sum((fd_current_value(f, today) for f in active_fds), ZERO)
    earned = sum((fd_accrued_interest(f.principal, f.interest_rate, f.start_date, f.maturity_date,
                                      f.compounding_frequency, f.payout_type, today) for f in active_fds), ZERO)
    projected_value = ZERO
    projected_interest = ZERO
    for f in active_fds:
        c = fd_calc(f, None)
        projected_value += c.gross_maturity_value
        projected_interest += c.total_interest
    rd_deposited = ZERO
    for r in active_rds:
        dep, acc = rd_progress(r.monthly_installment, r.interest_rate, r.start_date, r.tenure_months,
                               r.compounding_frequency, today)
        rd_deposited += dep
        current += dep + acc
        earned += acc
        c = rd_calc(r, None)
        projected_value += c.gross_maturity_value
        projected_interest += c.total_interest
    tax = estimate_tax(projected_interest, projected_value, tax_slab)
    return {
        "active_fd_count": len(active_fds),
        "active_rd_count": len(active_rds),
        "fd_principal": round_money(fd_principal),
        "rd_deposited_to_date": round_money(rd_deposited),
        "current_value": round_money(current),
        "interest_earned_to_date": round_money(earned),
        "projected_maturity_value": round_money(projected_value),
        "projected_total_interest": round_money(projected_interest),
        "estimated_tax_on_projected_interest": tax.estimated_tax,
        "unverified_rate_count": sum(1 for d in [*active_fds, *active_rds] if not d.rate_verified),
        "note": "Gross values from the rates you entered. Tax is an estimate. Active deposits only.",
    }


def upcoming_maturities(fds: list[FixedDeposit], rds: list[RecurringDeposit], today: date, within_days: int) -> list[dict]:
    items = []
    for f in fds:
        days = (f.maturity_date - today).days
        if f.status in OPEN_STATUSES and 0 <= days <= within_days:
            items.append({"id": f.id, "kind": "FD", "bank_name": f.bank_name, "maturity_date": f.maturity_date,
                          "days_to_maturity": days, "gross_maturity_value": fd_calc(f, None).gross_maturity_value,
                          "rate_verified": f.rate_verified, "source": f.source})
    for r in rds:
        days = (r.maturity_date - today).days
        if r.status in OPEN_STATUSES and 0 <= days <= within_days:
            items.append({"id": r.id, "kind": "RD", "bank_name": r.bank_name, "maturity_date": r.maturity_date,
                          "days_to_maturity": days, "gross_maturity_value": rd_calc(r, None).gross_maturity_value,
                          "rate_verified": r.rate_verified, "source": r.source})
    return sorted(items, key=lambda i: (i["maturity_date"], i["kind"], i["id"]))
