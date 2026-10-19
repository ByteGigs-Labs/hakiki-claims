import pytest
from sqlalchemy import func, select

from api.db.models import Tenant, User
from scripts.seed import ensure_demo_user


@pytest.fixture(autouse=True)
def demo_env(monkeypatch):
    monkeypatch.setenv("DEMO_TENANT_NAME", "Demo Hospital")
    monkeypatch.setenv("DEMO_USER_NAME", "Demo Clerk")
    monkeypatch.setenv("DEMO_USER_EMAIL", "Clerk@Demo.test")
    monkeypatch.setenv("DEMO_USER_PASSWORD", "demo-password-1")


def test_seed_creates_a_user_that_can_log_in(client, db):
    ensure_demo_user(db)
    response = client.post(
        "/v1/auth/login", json={"email": "clerk@demo.test", "password": "demo-password-1"}
    )
    assert response.status_code == 200 and response.json()["facility"] == "Demo Hospital"


def test_seed_is_idempotent(db):
    ensure_demo_user(db)
    ensure_demo_user(db)
    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert db.scalar(select(func.count()).select_from(Tenant)) == 1
