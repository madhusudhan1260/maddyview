"""Single source of 'now' so tests can freeze time. Dates are in Indian Standard Time."""

from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), "IST")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def today() -> date:
    return datetime.now(IST).date()
