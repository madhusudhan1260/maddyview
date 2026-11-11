"""Test fixtures. Tests run against a real PostgreSQL database (FINPILOT_TEST_DATABASE_URL),
migrated with Alembic, so NUMERIC types, constraints and migrations are exercised for real."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
TEST_DB_URL = os.environ.get("FINPILOT_TEST_DATABASE_URL", "postgresql+psycopg://localhost:5432/finpilot_test")
os.environ["FINPILOT_DATABASE_URL"] = TEST_DB_URL  # must be set before app modules import
os.environ["FINPILOT_AUTH_RATE_LIMIT_PER_MINUTE"] = "1000"
os.environ["FINPILOT_LOG_LEVEL"] = "WARNING"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.rate_limit import auth_limiter  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = "Correct-Horse-42"
ORIGIN = "http://localhost:5190"


def alembic(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", "-x", f"db_url={TEST_DB_URL}", *args], cwd=BACKEND, check=True,
                   capture_output=True)


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    alembic("downgrade", "base")
    alembic("upgrade", "head")
    yield


@pytest.fixture(autouse=True)
def clean_tables(migrated_db):
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    auth_limiter.reset()
    yield


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture
def client():
    with TestClient(app, base_url="http://testserver") as c:
        yield c


@pytest.fixture
def auth_client(client):
    r = client.post("/api/v1/auth/register", json={"email": "me@example.com", "display_name": "Me", "password": PASSWORD})
    assert r.status_code == 201, r.text
    return client
