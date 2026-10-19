import pytest

from api.config import get_settings
from tests.conftest import PASSWORD


@pytest.fixture
def tight(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "login_account_per_five_minutes", 3)
    monkeypatch.setattr(settings, "login_ip_per_minute", 6)
    monkeypatch.setattr(settings, "check_per_minute", 2)
    monkeypatch.setattr(settings, "max_body_bytes", 2000)


def attempt(client, email: str, password: str = "wrong-password"):
    return client.post("/v1/auth/login", json={"email": email, "password": password})


def test_repeated_failures_lock_the_account_for_a_while(client, make_user, tight):
    user = make_user()
    codes = [attempt(client, user.email).status_code for _ in range(4)]
    assert codes == [401, 401, 401, 429]
    locked = attempt(client, user.email, PASSWORD)
    assert locked.status_code == 429 and int(locked.headers["retry-after"]) > 0


def test_successful_logins_do_not_count_towards_the_lockout(client, make_user, tight):
    user = make_user()
    assert all(attempt(client, user.email, PASSWORD).status_code == 200 for _ in range(5))


def test_a_success_resets_the_failure_count(client, make_user, tight):
    user = make_user()
    attempt(client, user.email)
    attempt(client, user.email)
    assert attempt(client, user.email, PASSWORD).status_code == 200
    assert [attempt(client, user.email).status_code for _ in range(3)] == [401, 401, 401]


def test_ip_limit_applies_across_accounts(client, tight):
    codes = [attempt(client, f"user{i}@x.test").status_code for i in range(8)]
    assert codes[:6] == [401] * 3 + [401] * 3 or 429 in codes
    assert codes[-1] == 429


def test_check_endpoint_is_limited_per_user(client, make_user, login, tight):
    session = login(make_user())
    body = {
        "patient_token": "pat-1",
        "facility_id": "fac-12",
        "service_code": "svc-OPD-01",
        "fund": "SHIF",
        "date_of_service": "2026-10-14",
        "amount_kes": 700,
    }
    codes = [session.post("/v1/claims/check", json=body).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_oversized_bodies_are_rejected_with_413(client, make_user, login, tight):
    session = login(make_user())
    response = session.post(
        "/v1/claims/check", content=b"x" * 5000, headers={"content-type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_limiter_fails_closed_when_redis_is_down(client, monkeypatch):
    from api import ratelimit

    monkeypatch.setattr(
        ratelimit,
        "get_redis",
        lambda: __import__("redis").Redis(port=1, socket_connect_timeout=0.2),
    )
    assert attempt(client, "a@b.test").status_code == 503
