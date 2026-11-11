from datetime import date

import pytest

from app.core import clock

API = "/api/v1"
FD = {"bank_name": "My Bank", "principal": "100000", "interest_rate": "7", "start_date": "2026-01-01",
      "maturity_date": "2027-01-01", "compounding_frequency": "QUARTERLY", "payout_type": "CUMULATIVE"}
RD = {"bank_name": "My Bank", "monthly_installment": "1000", "interest_rate": "7", "start_date": "2026-01-01",
      "tenure_months": 12, "compounding_frequency": "QUARTERLY"}


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr(clock, "today", lambda: date(2026, 7, 1))


def test_fd_crud_with_calculation(auth_client):
    c = auth_client
    r = c.post(f"{API}/fixed-deposits", json=FD)
    assert r.status_code == 201, r.text
    fd = r.json()
    assert fd["rate_verified"] is False
    assert fd["calculation"]["gross_maturity_value"] == "107185.90"
    assert fd["interest_earned_to_date"] == "3530.63"
    assert fd["days_to_maturity"] == 184
    assert fd["calculation"]["tax"]["estimated_tax"] is None

    c.patch(f"{API}/settings", json={"tax_slab_percent": "30"})
    fd = c.get(f"{API}/fixed-deposits/{fd['id']}").json()
    assert fd["calculation"]["tax"]["estimated_tax"] == "2155.77"
    assert fd["calculation"]["tax"]["estimated_post_tax_value"] == "105030.13"

    r = c.patch(f"{API}/fixed-deposits/{fd['id']}", json={"rate_verified": True, "interest_rate": "7.25"})
    assert r.json()["rate_verified"] is True and r.json()["interest_rate"] == "7.25"
    assert c.patch(f"{API}/fixed-deposits/{fd['id']}", json={"maturity_date": "2025-01-01"}).status_code == 422
    assert c.delete(f"{API}/fixed-deposits/{fd['id']}").status_code == 204
    assert c.get(f"{API}/fixed-deposits").json() == []


def test_fd_validation(auth_client):
    c = auth_client
    for patch in ({"maturity_date": "2025-12-31"}, {"principal": "0"}, {"interest_rate": "45"},
                  {"payout_type": "WEEKLY"}, {"compounding_frequency": "DAILY"}):
        assert c.post(f"{API}/fixed-deposits", json={**FD, **patch}).status_code == 422, patch


def test_fd_calculate_preview_does_not_save(auth_client):
    body = {k: v for k, v in FD.items() if k != "bank_name"} | {"payout_type": "MONTHLY_PAYOUT"}
    r = auth_client.post(f"{API}/fixed-deposits/calculate", json=body)
    assert r.json()["periodic_payout"] == "583.33"
    assert auth_client.get(f"{API}/fixed-deposits").json() == []


def test_rd_crud_derives_maturity(auth_client):
    c = auth_client
    r = c.post(f"{API}/recurring-deposits", json=RD)
    assert r.status_code == 201, r.text
    rd = r.json()
    assert rd["maturity_date"] == "2027-01-01"
    assert rd["calculation"]["gross_maturity_value"] == "12462.13"
    assert rd["deposited_to_date"] == "7000.00"
    bad = c.post(f"{API}/recurring-deposits", json={**RD, "maturity_date": "2027-03-01"})
    assert bad.status_code == 422
    r = c.patch(f"{API}/recurring-deposits/{rd['id']}", json={"tenure_months": 24})
    assert r.json()["maturity_date"] == "2028-01-01"
    assert c.delete(f"{API}/recurring-deposits/{rd['id']}").status_code == 204


def test_rd_calculate_preview(auth_client):
    r = auth_client.post(f"{API}/recurring-deposits/calculate",
                         json={"monthly_installment": "1000", "interest_rate": "6", "tenure_months": 12, "compounding_frequency": "SIMPLE"})
    assert r.json()["total_interest"] == "390.00"


def test_deposit_summary_and_upcoming(auth_client):
    c = auth_client
    c.post(f"{API}/fixed-deposits", json={**FD, "maturity_date": "2026-08-01"})  # matures in 31 days
    c.post(f"{API}/fixed-deposits", json={**FD, "status": "CLOSED"})  # excluded
    c.post(f"{API}/recurring-deposits", json=RD)
    s = c.get(f"{API}/deposits/summary").json()
    assert s["active_fd_count"] == 1 and s["active_rd_count"] == 1
    assert s["fd_principal"] == "100000.00"
    assert s["rd_deposited_to_date"] == "7000.00"
    assert s["unverified_rate_count"] == 2
    up = c.get(f"{API}/deposits/upcoming-maturities?days=60").json()
    assert [(u["kind"], u["days_to_maturity"]) for u in up] == [("FD", 31)]
    assert len(c.get(f"{API}/deposits/upcoming-maturities?days=365").json()) == 2


def test_empty_deposit_summary(auth_client):
    s = auth_client.get(f"{API}/deposits/summary").json()
    assert s["active_fd_count"] == 0 and s["current_value"] == "0.00"
    assert auth_client.get(f"{API}/deposits/upcoming-maturities").json() == []


def test_savings_goal_crud(auth_client):
    c = auth_client
    r = c.post(f"{API}/savings-goals", json={"name": "Emergency fund", "target_amount": "100000", "current_amount": "20000",
                                             "monthly_contribution": "5000", "target_date": "2027-07-01"})
    assert r.status_code == 201
    g = r.json()
    assert g["projection"]["progress_percent"] == "20"
    assert g["projection"]["months_to_goal"] == 16
    assert g["projection"]["projection_type"] == "DETERMINISTIC"
    r = c.patch(f"{API}/savings-goals/{g['id']}", json={"current_amount": "100000"})
    assert r.json()["projection"]["progress_percent"] == "100"
    assert c.post(f"{API}/savings-goals", json={"name": "x", "target_amount": "0"}).status_code == 422
    assert c.delete(f"{API}/savings-goals/{g['id']}").status_code == 204


def test_investment_goal_is_labelled_as_assumption(auth_client):
    r = auth_client.post(f"{API}/investment-goals", json={"name": "Retirement", "target_amount": "1000000", "current_amount": "100000",
                                                          "monthly_contribution": "10000", "expected_annual_return_percent": "12"})
    assert r.status_code == 201
    p = r.json()["projection"]
    assert p["projection_type"] == "ASSUMED_RETURN"
    assert "not guaranteed" in p["assumption"]
    assert auth_client.post(f"{API}/investment-goals", json={"name": "x", "target_amount": "10",
                                                             "expected_annual_return_percent": "80"}).status_code == 422
