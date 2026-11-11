from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError, StatementError

from app.core import clock
from app.core.security import hash_password
from app.database.session import engine
from app.models import (
    BankAccount,
    ExpenseRecord,
    FixedDeposit,
    Holding,
    IncomeRecord,
    Instrument,
    Portfolio,
    User,
    UserSettings,
)
from app.models.enums import CompoundingFrequency, InstrumentType, PaymentMethod, PayoutType

API = "/api/v1"


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr(clock, "today", lambda: date(2026, 11, 11))


# ---------- empty state ----------
def test_dashboard_empty_account(auth_client):
    d = auth_client.get(f"{API}/dashboard").json()
    assert d["net_worth"] == {"total_assets": "0.00", "total_liabilities": "0.00", "net_worth": "0.00",
                              "bank_balances": "0.00", "fixed_deposits": "0.00", "recurring_deposits": "0.00",
                              "investments_at_cost": "0.00"}
    assert d["month"]["savings_rate"] is None
    assert d["allocation"] == [] and d["recent_transactions"] == [] and d["upcoming_maturities"] == []
    assert d["goals"]["overall_progress_percent"] is None
    assert d["ai_reports"] == [] and "None have been generated" in d["ai_reports_note"]
    assert d["includes_demo"] is False


def test_dashboard_aggregates_user_data(auth_client):
    c = auth_client
    c.post(f"{API}/bank-accounts", json={"bank_name": "B", "account_label": "S", "account_type": "SAVINGS", "balance": "50000"})
    c.post(f"{API}/liabilities", json={"name": "Card", "liability_type": "CREDIT_CARD", "outstanding_amount": "12000"})
    c.post(f"{API}/income", json={"amount": "80000", "income_source": "Job", "category": "Salary", "record_date": "2026-11-01"})
    c.post(f"{API}/expenses", json={"amount": "20000", "category": "Rent", "record_date": "2026-11-02", "payment_method": "UPI"})
    c.post(f"{API}/fixed-deposits", json={"bank_name": "B", "principal": "100000", "interest_rate": "7", "start_date": "2026-11-11",
                                          "maturity_date": "2027-01-01", "compounding_frequency": "QUARTERLY", "payout_type": "CUMULATIVE"})
    c.post(f"{API}/savings-goals", json={"name": "Trip", "target_amount": "10000", "current_amount": "2500"})
    d = c.get(f"{API}/dashboard").json()
    nw = d["net_worth"]
    assert nw["bank_balances"] == "50000.00"
    assert nw["fixed_deposits"] == "100000.00"  # starts today: no interest accrued yet
    assert nw["total_assets"] == "150000.00"
    assert nw["total_liabilities"] == "12000.00"
    assert nw["net_worth"] == "138000.00"
    assert d["month"] == {"month": "2026-11", "income": "80000.00", "expenses": "20000.00", "savings": "60000.00", "savings_rate": "75.00"}
    assert {a["asset_class"]: a["percent"] for a in d["allocation"]} == {"Bank balances": "33.33", "Fixed deposits": "66.67"}
    assert d["goals"]["overall_progress_percent"] == "25.00"
    assert len(d["recent_transactions"]) == 2
    assert d["upcoming_maturities"][0]["days_to_maturity"] == 51


# ---------- DEMO separation ----------
def test_demo_data_is_labelled_and_separable(auth_client):
    c = auth_client
    c.post(f"{API}/income", json={"amount": "1000", "income_source": "Me", "category": "Gift", "record_date": "2026-11-01"})
    assert c.post(f"{API}/demo").status_code == 200
    assert c.get(f"{API}/settings").json()["include_demo_data"] is True
    rows = c.get(f"{API}/income").json()
    assert {r["source"] for r in rows} == {"USER_ENTERED", "DEMO"}
    d = c.get(f"{API}/dashboard").json()
    assert d["includes_demo"] is True and d["net_worth"]["total_liabilities"] == "340000.00"

    c.patch(f"{API}/settings", json={"include_demo_data": False})
    assert {r["source"] for r in c.get(f"{API}/income").json()} == {"USER_ENTERED"}
    assert c.get(f"{API}/dashboard").json()["net_worth"]["total_liabilities"] == "0.00"

    r = c.delete(f"{API}/demo")
    assert r.status_code == 200
    c.patch(f"{API}/settings", json={"include_demo_data": True})
    assert {r["source"] for r in c.get(f"{API}/income").json()} == {"USER_ENTERED"}
    assert c.get(f"{API}/demo").json()["has_demo_data"] is False


def test_settings_tax_slab_set_and_clear(auth_client):
    c = auth_client
    assert c.patch(f"{API}/settings", json={"tax_slab_percent": "20"}).json()["tax_slab_percent"] == "20"
    assert c.patch(f"{API}/settings", json={"theme": "LIGHT"}).json()["tax_slab_percent"] == "20"
    assert c.patch(f"{API}/settings", json={"tax_slab_percent": None}).json()["tax_slab_percent"] is None
    assert c.patch(f"{API}/settings", json={"tax_slab_percent": "60"}).status_code == 422


def test_audit_log_records_crud(auth_client):
    c = auth_client
    r = c.post(f"{API}/expenses", json={"amount": "5", "category": "x", "record_date": "2026-11-01", "payment_method": "CASH"})
    c.delete(f"{API}/expenses/{r.json()['id']}")
    actions = [a["action"] for a in c.get(f"{API}/audit-logs").json()]
    assert actions[:2] == ["expense.delete", "expense.create"]


# ---------- database relationships & constraints ----------
def make_user(db) -> User:
    u = User(email="db@example.com", display_name="DB", password_hash=hash_password("x"))
    u.settings = UserSettings()
    db.add(u)
    db.commit()
    return u


def test_money_columns_are_numeric(db):
    cols = {c["name"]: c["type"] for c in inspect(engine).get_columns("income_records")}
    assert str(cols["amount"]) == "NUMERIC(18, 2)"
    u = make_user(db)
    db.add(IncomeRecord(user_id=u.id, amount=Decimal("0.10"), income_source="a", category="a", record_date=date(2026, 1, 1)))
    db.add(IncomeRecord(user_id=u.id, amount=Decimal("0.20"), income_source="a", category="a", record_date=date(2026, 1, 1)))
    db.commit()
    total = sum(db.scalars(select(IncomeRecord.amount)))
    assert isinstance(total, Decimal) and total == Decimal("0.30")


def test_deleting_user_cascades(db):
    u = make_user(db)
    acct = BankAccount(user_id=u.id, bank_name="b", account_label="l", account_type="SAVINGS", balance=Decimal("1"))
    db.add(acct)
    db.flush()
    db.add(ExpenseRecord(user_id=u.id, bank_account_id=acct.id, amount=Decimal("1"), category="c",
                         record_date=date(2026, 1, 1), payment_method=PaymentMethod.CASH))
    db.commit()
    db.delete(u)
    db.commit()
    assert db.scalar(select(ExpenseRecord)) is None
    assert db.scalar(select(BankAccount)) is None
    assert db.scalar(select(UserSettings)) is None


def test_deleting_bank_account_keeps_records(db):
    u = make_user(db)
    acct = BankAccount(user_id=u.id, bank_name="b", account_label="l", account_type="SAVINGS", balance=Decimal("1"))
    db.add(acct)
    db.flush()
    db.add(IncomeRecord(user_id=u.id, bank_account_id=acct.id, amount=Decimal("1"), income_source="s", category="c",
                        record_date=date(2026, 1, 1)))
    db.commit()
    db.delete(acct)
    db.commit()
    assert db.scalar(select(IncomeRecord)).bank_account_id is None


@pytest.mark.parametrize("bad", [
    {"principal": Decimal("-1")},
    {"maturity_date": date(2025, 1, 1)},
    {"interest_rate": Decimal("50")},
    {"source": "FAKE"},
])
def test_fd_check_constraints(db, bad):
    u = make_user(db)
    data = dict(user_id=u.id, bank_name="b", principal=Decimal("1000"), interest_rate=Decimal("7"), start_date=date(2026, 1, 1),
                maturity_date=date(2027, 1, 1), compounding_frequency=CompoundingFrequency.QUARTERLY, payout_type=PayoutType.CUMULATIVE)
    data.update(bad)
    with pytest.raises(StatementError):  # IntegrityError from Postgres, or ORM-side enum validation
        db.add(FixedDeposit(**data))
        db.commit()
    db.rollback()


def test_database_rejects_unknown_source_label_even_via_raw_sql(db):
    from sqlalchemy import text
    u = make_user(db)
    with pytest.raises(IntegrityError):
        db.execute(text("INSERT INTO income_records (user_id, amount, income_source, category, record_date, source) "
                        "VALUES (:u, 1, 'a', 'a', '2026-01-01', 'FAKE')"), {"u": u.id})
    db.rollback()


def test_holdings_relationships_and_uniqueness(db):
    u = make_user(db)
    inst = Instrument(instrument_type=InstrumentType.STOCK, symbol="TEST", name="Test Co", exchange="NSE", source="DEMO")
    pf = Portfolio(user_id=u.id, name="Main")
    db.add_all([inst, pf])
    db.flush()
    db.add(Holding(portfolio_id=pf.id, instrument_id=inst.id, quantity=Decimal("10"), avg_cost=Decimal("100.5")))
    db.commit()
    assert pf.holdings[0].instrument.symbol == "TEST"
    with pytest.raises(IntegrityError):
        db.add(Holding(portfolio_id=pf.id, instrument_id=inst.id, quantity=Decimal("1"), avg_cost=Decimal("1")))
        db.commit()
    db.rollback()
    with pytest.raises(IntegrityError):  # instrument in use cannot be deleted (RESTRICT)
        db.delete(inst)
        db.commit()
    db.rollback()


def test_all_milestone_tables_exist():
    expected = {
        "users", "user_settings", "income_records", "expense_records", "bank_accounts", "transactions", "instruments",
        "portfolios", "holdings", "investment_transactions", "fixed_deposits", "recurring_deposits", "savings_goals",
        "investment_goals", "monthly_budgets", "news_articles", "market_data_sources", "data_ingestion_logs",
        "model_registry", "model_predictions", "prediction_results", "paper_accounts", "paper_orders", "paper_positions",
        "paper_trades", "audit_logs", "alerts", "auth_sessions", "liabilities",
    }
    assert expected <= set(inspect(engine).get_table_names())
