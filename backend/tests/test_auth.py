from datetime import timedelta

from sqlalchemy import select

from app.core.rate_limit import auth_limiter
from app.core.security import hash_password, verify_password
from app.models import AuditLog, AuthSession, User
from tests.conftest import ORIGIN, PASSWORD

API = "/api/v1"


def test_password_hash_is_argon2id():
    h = hash_password(PASSWORD)
    assert h.startswith("$argon2id$")
    assert verify_password(h, PASSWORD)
    assert not verify_password(h, "wrong")
    assert not verify_password("not-a-hash", PASSWORD)


def test_status_before_setup(client):
    r = client.get(f"{API}/auth/status")
    assert r.json() == {"setup_required": True, "authenticated": False, "user": None}


def test_register_sets_httponly_cookie_and_stores_only_token_hash(client, db):
    r = client.post(f"{API}/auth/register", json={"email": "Me@Example.com", "display_name": "Me", "password": PASSWORD})
    assert r.status_code == 201
    cookie = r.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/api" in cookie
    token = client.cookies.get("finpilot_session")
    user = db.scalar(select(User))
    assert user.email == "me@example.com"
    assert user.password_hash.startswith("$argon2id$") and PASSWORD not in user.password_hash
    sess = db.scalar(select(AuthSession))
    assert sess.token_hash != token and len(sess.token_hash) == 64
    assert "password_hash" not in r.text


def test_only_one_account_can_be_registered(auth_client):
    r = auth_client.post(f"{API}/auth/register", json={"email": "x@example.com", "display_name": "X", "password": PASSWORD})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "setup_complete"


def test_weak_password_rejected(client):
    r = client.post(f"{API}/auth/register", json={"email": "a@example.com", "display_name": "A", "password": "short"})
    assert r.status_code == 422
    r = client.post(f"{API}/auth/register", json={"email": "a@example.com", "display_name": "A", "password": "alllowercaseletters"})
    assert r.status_code == 422


def test_login_logout_cycle(auth_client, db):
    auth_client.post(f"{API}/auth/logout")
    assert auth_client.get(f"{API}/auth/me").status_code == 401
    bad = auth_client.post(f"{API}/auth/login", json={"email": "me@example.com", "password": "Wrong-Password-1"})
    assert bad.status_code == 401
    assert bad.json()["error"]["message"] == "Invalid email or password"
    unknown = auth_client.post(f"{API}/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert unknown.json()["error"]["message"] == "Invalid email or password"  # no user enumeration
    ok = auth_client.post(f"{API}/auth/login", json={"email": "me@example.com", "password": PASSWORD})
    assert ok.status_code == 200
    assert auth_client.get(f"{API}/auth/me").json()["email"] == "me@example.com"
    actions = list(db.scalars(select(AuditLog.action)))
    assert {"auth.register", "auth.logout", "auth.login_failed", "auth.login"} <= set(actions)


def test_protected_routes_require_session(client):
    for path in ("/dashboard", "/income", "/fixed-deposits", "/savings-goals", "/settings"):
        r = client.get(f"{API}{path}")
        assert r.status_code == 401, path
        assert r.json()["error"]["code"] == "unauthorized"


def test_expired_session_rejected(auth_client, db):
    sess = db.scalar(select(AuthSession))
    sess.expires_at = sess.expires_at - timedelta(days=30)
    db.commit()
    assert auth_client.get(f"{API}/auth/me").status_code == 401


def test_forged_cookie_rejected(client):
    client.cookies.set("finpilot_session", "forged-token", path="/api")
    assert client.get(f"{API}/auth/me").status_code == 401


def test_cross_origin_writes_blocked(auth_client):
    r = auth_client.post(f"{API}/income", headers={"origin": "https://evil.example"},
                         json={"amount": "1", "income_source": "x", "category": "x", "record_date": "2026-01-01"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden_origin"
    r = auth_client.post(f"{API}/income", headers={"origin": ORIGIN},
                         json={"amount": "1", "income_source": "x", "category": "x", "record_date": "2026-01-01"})
    assert r.status_code == 201


def test_login_rate_limited(client):
    old = auth_limiter.limit
    auth_limiter.limit = 3
    try:
        codes = [client.post(f"{API}/auth/login", json={"email": "a@example.com", "password": "x"}).status_code for _ in range(5)]
    finally:
        auth_limiter.limit = old
    assert codes[:3] == [401, 401, 401]
    assert codes[3:] == [429, 429]


def test_security_headers(client):
    r = client.get(f"{API}/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-request-id"]
