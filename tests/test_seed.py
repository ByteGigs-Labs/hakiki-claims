import pytest
from sqlalchemy import func, select

from api.db.models import ClaimChecked, Tenant, User
from scripts.seed import ensure_demo_user, load_synthetic_claims


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


def test_seed_loads_the_synthetic_claims_once_and_spreads_them_over_four_weeks(db):
    user = ensure_demo_user(db)
    assert load_synthetic_claims(db, user) == 44
    assert load_synthetic_claims(db, user) == 0
    refs = db.scalars(select(ClaimChecked.claim_ref)).all()
    assert len(set(refs)) == 44 and len(refs) > 44
    first, last = db.execute(
        select(func.min(ClaimChecked.checked_at), func.max(ClaimChecked.checked_at))
    ).one()
    assert (last - first).days >= 26


def test_seeded_demo_shows_protected_revenue_on_the_overview(db):
    from api.services.reports import overview

    user = ensure_demo_user(db)
    load_synthetic_claims(db, user)
    report = overview(db, user.tenant_id, 30)
    assert report["claims"] == 44 and report["claims_protected"] >= 5
    assert report["revenue_protected_kes"] > 0 and report["revenue_at_risk_kes"] > 0
    assert len({day["date"] for day in report["daily"] if day["checks"]}) >= 20
