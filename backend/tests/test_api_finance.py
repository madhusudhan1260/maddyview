from app.core import clock

API = "/api/v1"


def add_income(c, amount="50000.00", date="2026-03-01", category="Salary", **kw):
    r = c.post(f"{API}/income", json={"amount": amount, "income_source": "Employer", "category": category,
                                      "record_date": date, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def add_expense(c, amount="1000.00", date="2026-03-05", category="Food", method="UPI", **kw):
    r = c.post(f"{API}/expenses", json={"amount": amount, "category": category, "record_date": date,
                                        "payment_method": method, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    r = client.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok" and r.json()["database"] == "ok"


def test_income_crud(auth_client):
    c = auth_client
    inc = add_income(c, description="March salary")
    assert inc["amount"] == "50000.00" and inc["source"] == "USER_ENTERED"
    r = c.patch(f"{API}/income/{inc['id']}", json={"amount": "52000.5", "description": None})
    assert r.status_code == 200
    assert r.json()["amount"] == "52000.50" and r.json()["description"] is None
    assert c.get(f"{API}/income/{inc['id']}").json()["category"] == "Salary"
    assert c.delete(f"{API}/income/{inc['id']}").status_code == 204
    assert c.get(f"{API}/income/{inc['id']}").status_code == 404
    assert c.get(f"{API}/income").json() == []


def test_expense_crud(auth_client):
    c = auth_client
    e = add_expense(c, description="Lunch")
    r = c.patch(f"{API}/expenses/{e['id']}", json={"payment_method": "CREDIT_CARD", "category": "Dining"})
    assert r.json()["payment_method"] == "CREDIT_CARD" and r.json()["category"] == "Dining"
    assert c.delete(f"{API}/expenses/{e['id']}").status_code == 204
    assert c.delete(f"{API}/expenses/{e['id']}").status_code == 404


def test_client_cannot_set_source_label(auth_client):
    r = auth_client.post(f"{API}/income", json={"amount": "10", "income_source": "x", "category": "x",
                                                "record_date": "2026-01-01", "source": "REAL"})
    assert r.status_code == 201
    assert r.json()["source"] == "USER_ENTERED"


def test_validation_errors(auth_client):
    c = auth_client
    cases = [
        {"amount": "0", "income_source": "x", "category": "x", "record_date": "2026-01-01"},
        {"amount": "-5", "income_source": "x", "category": "x", "record_date": "2026-01-01"},
        {"amount": "10.123", "income_source": "x", "category": "x", "record_date": "2026-01-01"},
        {"amount": "10", "income_source": "  ", "category": "x", "record_date": "2026-01-01"},
        {"amount": "10", "income_source": "x", "category": "x", "record_date": "not-a-date"},
        {"amount": "abc", "income_source": "x", "category": "x", "record_date": "2026-01-01"},
    ]
    for body in cases:
        r = c.post(f"{API}/income", json=body)
        assert r.status_code == 422, body
        assert r.json()["error"]["code"] == "validation_error"
    r = c.post(f"{API}/expenses", json={"amount": "5", "category": "x", "record_date": "2026-01-01", "payment_method": "BITCOIN"})
    assert r.status_code == 422
    inc = add_income(c)
    r = c.patch(f"{API}/income/{inc['id']}", json={"amount": None})
    assert r.status_code == 422
    assert c.get(f"{API}/income?month=2026-13").status_code == 422


def test_filters_by_month_and_category(auth_client):
    c = auth_client
    add_income(c, date="2026-02-28")
    add_income(c, date="2026-03-01", category="Bonus", amount="5000")
    add_expense(c, date="2026-03-31", category="Rent", amount="20000")
    add_expense(c, date="2026-04-01", category="Rent", amount="20000")
    add_expense(c, date="2026-03-10", category="Food", amount="3000")
    assert len(c.get(f"{API}/income?month=2026-03").json()) == 1
    assert len(c.get(f"{API}/expenses?month=2026-03").json()) == 2
    assert len(c.get(f"{API}/expenses?category=Rent").json()) == 2
    assert len(c.get(f"{API}/expenses?month=2026-03&category=Rent").json()) == 1
    assert c.get(f"{API}/expense-categories").json() == ["Food", "Rent"]


def test_monthly_summary_and_breakdown(auth_client):
    c = auth_client
    add_income(c, amount="60000", date="2026-03-01")
    add_expense(c, amount="15000", category="Rent", date="2026-03-02")
    add_expense(c, amount="5000.50", category="Food", date="2026-03-03")
    s = c.get(f"{API}/finance/summary?month=2026-03").json()
    assert s["total_income"] == "60000.00"
    assert s["total_expenses"] == "20000.50"
    assert s["savings"] == "39999.50"
    assert s["savings_rate"] == "66.67"
    assert [b["category"] for b in s["expense_breakdown"]] == ["Rent", "Food"]
    assert s["expense_breakdown"][0]["percent"] == "75"


def test_zero_income_summary(auth_client):
    add_expense(auth_client, amount="100", date="2026-03-02")
    s = auth_client.get(f"{API}/finance/summary?month=2026-03").json()
    assert s["savings_rate"] is None
    assert "No income" in s["savings_rate_note"]
    assert s["savings"] == "-100.00"


def test_transaction_history_merges_and_sorts(auth_client):
    c = auth_client
    add_income(c, date="2026-03-01")
    add_expense(c, date="2026-03-05")
    add_expense(c, date="2026-02-05")
    rows = c.get(f"{API}/finance/transactions").json()
    assert [r["record_date"] for r in rows] == ["2026-03-05", "2026-03-01", "2026-02-05"]
    assert rows[0]["kind"] == "EXPENSE" and rows[0]["label"] == "UPI"
    assert len(c.get(f"{API}/finance/transactions?kind=INCOME").json()) == 1


def test_trend(auth_client, monkeypatch):
    from datetime import date
    monkeypatch.setattr(clock, "today", lambda: date(2026, 3, 20))
    add_income(auth_client, amount="1000", date="2026-03-01")
    add_income(auth_client, amount="500", date="2026-01-01")
    t = auth_client.get(f"{API}/finance/trend?months=3").json()
    assert [p["month"] for p in t] == ["2026-01", "2026-02", "2026-03"]
    assert [p["income"] for p in t] == ["500.00", "0.00", "1000.00"]


def test_bank_accounts_and_liabilities(auth_client):
    c = auth_client
    r = c.post(f"{API}/bank-accounts", json={"bank_name": "My Bank", "account_label": "Salary", "account_type": "SALARY",
                                             "last4": "1234", "balance": "15000.75"})
    assert r.status_code == 201 and r.json()["balance"] == "15000.75"
    assert c.post(f"{API}/bank-accounts", json={"bank_name": "B", "account_label": "x", "account_type": "SAVINGS",
                                                "last4": "12345678", "balance": "1"}).status_code == 422
    acct = r.json()["id"]
    inc = add_income(c, bank_account_id=acct)
    assert inc["bank_account_id"] == acct
    r = c.post(f"{API}/income", json={"amount": "1", "income_source": "x", "category": "x", "record_date": "2026-01-01",
                                      "bank_account_id": 99999})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_reference"
    l = c.post(f"{API}/liabilities", json={"name": "Home loan", "liability_type": "HOME_LOAN", "outstanding_amount": "2500000",
                                           "interest_rate": "8.5", "emi_amount": "22000"})
    assert l.status_code == 201 and l.json()["interest_rate"] == "8.5"
    assert len(c.get(f"{API}/liabilities").json()) == 1


def test_users_cannot_see_each_others_records(auth_client, db):
    """Repository queries are scoped by user_id even though the app is single-user."""
    from app.core.security import hash_password
    from app.models import IncomeRecord, User
    other = User(email="other@example.com", display_name="Other", password_hash=hash_password("x"))
    db.add(other)
    db.flush()
    from datetime import date
    rec = IncomeRecord(user_id=other.id, amount=1, income_source="x", category="x", record_date=date(2026, 1, 1))
    db.add(rec)
    db.commit()
    assert auth_client.get(f"{API}/income").json() == []
    assert auth_client.get(f"{API}/income/{rec.id}").status_code == 404
    assert auth_client.delete(f"{API}/income/{rec.id}").status_code == 404
