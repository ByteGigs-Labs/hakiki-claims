from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import update

from api.db.models import UserSession
from api.security import Principal, Role, require_roles
from tests.conftest import PASSWORD


def credentials(user, password: str = PASSWORD) -> dict:
    return {"email": user.email, "password": password}


def test_login_returns_identity_and_sets_hardened_cookie(client, make_user):
    user = make_user()
    response = client.post("/v1/auth/login", json=credentials(user))
    cookie = response.headers["set-cookie"].lower()
    assert response.status_code == 200
    assert response.json()["facility"] == "Mercy Hospital"
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/" in cookie


def test_email_is_case_insensitive(client, make_user):
    make_user("clerk@mercy.test")
    response = client.post(
        "/v1/auth/login", json={"email": " Clerk@Mercy.test ", "password": PASSWORD}
    )
    assert response.status_code == 200


def test_unknown_email_and_wrong_password_look_identical(client, make_user):
    user = make_user()
    unknown = client.post("/v1/auth/login", json={"email": "no@one.test", "password": PASSWORD})
    wrong = client.post("/v1/auth/login", json=credentials(user, "wrong-password"))
    assert (unknown.status_code, unknown.json()) == (wrong.status_code, wrong.json())
    assert unknown.status_code == 401
    assert "set-cookie" not in unknown.headers


def test_inactive_user_cannot_log_in(client, make_user):
    user = make_user(active=False)
    assert client.post("/v1/auth/login", json=credentials(user)).status_code == 401


def test_oversized_password_is_rejected(client, make_user):
    user = make_user()
    assert client.post("/v1/auth/login", json=credentials(user, "x" * 5000)).status_code == 422


def test_me_requires_a_session(client):
    assert client.get("/v1/auth/me").status_code == 401


def test_me_returns_the_logged_in_user(client, make_user, login):
    user = make_user()
    body = login(user).get("/v1/auth/me").json()
    assert (body["name"], body["facility"], body["role"]) == (
        "Test User",
        "Mercy Hospital",
        "clerk",
    )


def test_logout_ends_the_session(client, make_user, login):
    session = login(make_user())
    assert session.post("/v1/auth/logout").status_code == 204
    assert session.get("/v1/auth/me").status_code == 401


def test_logout_revokes_the_token_server_side(client, make_user, login, db):
    session = login(make_user())
    token = session.cookies.get("hakiki_session")
    session.post("/v1/auth/logout")
    client.cookies.set("hakiki_session", token)
    assert client.get("/v1/auth/me").status_code == 401
    assert db.query(UserSession).count() == 0


def test_expired_session_is_rejected(client, make_user, login, db):
    session = login(make_user())
    db.execute(update(UserSession).values(expires_at=datetime.now(UTC) - timedelta(minutes=1)))
    db.commit()
    assert session.get("/v1/auth/me").status_code == 401


def test_deactivated_user_loses_access(client, make_user, login, db):
    user = make_user()
    session = login(user)
    user.is_active = False
    db.commit()
    assert session.get("/v1/auth/me").status_code == 401


def test_forged_cookie_is_rejected(client):
    client.cookies.set("hakiki_session", "forged-token")
    assert client.get("/v1/auth/me").status_code == 401


def test_cors_allows_the_dashboard_with_credentials(client):
    response = client.options(
        "/v1/auth/login",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_rejects_other_origins(client):
    response = client.get("/health", headers={"Origin": "https://evil.test"})
    assert "access-control-allow-origin" not in response.headers


def test_roles_are_enforced(make_user, login, client):
    probe = FastAPI()

    @probe.get("/admin-only")
    def admin_only(principal: Principal = Depends(require_roles(Role.ADMIN))):
        return {"role": principal.role}

    clerk, admin = make_user("c@mercy.test"), make_user("a@mercy.test", role=Role.ADMIN)
    login(clerk)
    probe_client = TestClient(probe, cookies=client.cookies)
    assert probe_client.get("/admin-only").status_code == 403
    client.cookies.clear()
    login(admin)
    probe_client = TestClient(probe, cookies=client.cookies)
    assert probe_client.get("/admin-only").json() == {"role": "admin"}
