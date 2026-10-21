import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from api.config import get_settings
from api.db.models import User, UserSession
from api.security import Role

from .conftest import PASSWORD

NEW_PASSWORD = "a-brand-new-passphrase"


@pytest.fixture
def admin(make_user, login):
    return make_user("admin@mercy.test", role=Role.ADMIN)


def person(**overrides) -> dict:
    return {
        "name": "Wanjiru Kamau",
        "email": "wanjiru@mercy.test",
        "role": "clerk",
        "password": "initial-passphrase",
        **overrides,
    }


def sign_in(client, email: str, password: str = PASSWORD) -> TestClient:
    session = TestClient(client.app)
    response = session.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return session


def test_an_admin_adds_a_user_who_can_log_in(client, admin):
    session = sign_in(client, admin.email)
    created = session.post("/v1/users", json=person(email="  Wanjiru@Mercy.TEST ")).json()
    assert created["email"] == "wanjiru@mercy.test" and created["role"] == "clerk"
    assert "password" not in created and "password_hash" not in created
    login = sign_in(client, "wanjiru@mercy.test", "initial-passphrase")
    assert login.get("/v1/auth/me").json()["facility"] == "Mercy Hospital"


def test_listing_shows_only_the_own_tenant(client, admin, make_user, make_tenant):
    make_user("other@elsewhere.test", make_tenant("Elsewhere"), Role.ADMIN)
    session = sign_in(client, admin.email)
    session.post("/v1/users", json=person())
    emails = [item["email"] for item in session.get("/v1/users").json()]
    assert sorted(emails) == ["admin@mercy.test", "wanjiru@mercy.test"]


@pytest.mark.parametrize("role", [Role.CLERK, Role.FINANCE_MANAGER])
def test_only_admins_manage_users(client, make_user, login, role):
    session = login(make_user("staff@mercy.test", role=role))
    assert session.get("/v1/users").status_code == 403
    assert session.post("/v1/users", json=person()).status_code == 403


def test_users_cannot_be_managed_without_login(client):
    assert client.get("/v1/users").status_code == 401


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "short"},
        {"email": "not-an-email"},
        {"role": "superuser"},
        {"name": ""},
        {"is_admin": True},
    ],
)
def test_invalid_new_users_are_rejected(client, admin, overrides):
    session = sign_in(client, admin.email)
    assert session.post("/v1/users", json=person(**overrides)).status_code == 422


def test_duplicate_emails_are_rejected_case_insensitively(client, admin):
    session = sign_in(client, admin.email)
    assert session.post("/v1/users", json=person()).status_code == 201
    again = session.post("/v1/users", json=person(email="WANJIRU@mercy.test"))
    assert again.status_code == 409


def test_roles_can_be_changed(client, admin, make_user, db):
    clerk = make_user("clerk@mercy.test", db.get(User, admin.id).tenant)
    session = sign_in(client, admin.email)
    changed = session.patch(f"/v1/users/{clerk.id}", json={"role": "finance_manager"})
    assert changed.json()["role"] == "finance_manager"


def test_a_deactivated_user_cannot_log_in_and_their_session_ends(client, admin, make_user, db):
    clerk = make_user("clerk@mercy.test", db.get(User, admin.id).tenant)
    clerk_session = sign_in(client, clerk.email)
    session = sign_in(client, admin.email)
    assert session.patch(f"/v1/users/{clerk.id}", json={"is_active": False}).status_code == 200
    assert clerk_session.get("/v1/auth/me").status_code == 401
    login = TestClient(client.app).post(
        "/v1/auth/login", json={"email": clerk.email, "password": PASSWORD}
    )
    assert login.status_code == 401
    assert session.patch(f"/v1/users/{clerk.id}", json={"is_active": True}).status_code == 200
    sign_in(client, clerk.email)


def test_an_admin_cannot_demote_or_deactivate_themselves(client, admin, make_user, db):
    make_user("second@mercy.test", db.get(User, admin.id).tenant, Role.ADMIN)
    session = sign_in(client, admin.email)
    assert session.patch(f"/v1/users/{admin.id}", json={"role": "clerk"}).status_code == 409
    assert session.patch(f"/v1/users/{admin.id}", json={"is_active": False}).status_code == 409
    assert session.patch(f"/v1/users/{admin.id}", json={"role": "admin"}).status_code == 200


def test_the_last_admin_cannot_be_removed(client, admin, make_user, db):
    from api.routes import users

    other = make_user("second@mercy.test", db.get(User, admin.id).tenant, Role.ADMIN)
    assert users._other_active_admins(db, other) == 1
    session = sign_in(client, admin.email)
    assert session.patch(f"/v1/users/{other.id}", json={"role": "clerk"}).status_code == 200
    assert users._other_active_admins(db, db.get(User, admin.id)) == 0


def test_the_last_admin_rule_blocks_the_only_remaining_admin(client, admin, db, monkeypatch):
    from api.routes import users

    session = sign_in(client, admin.email)
    monkeypatch.setattr(users, "_other_active_admins", lambda *_: 0)
    other = User(
        tenant_id=admin.tenant_id,
        email="second@mercy.test",
        name="Second",
        password_hash="x",
        role="admin",
    )
    db.add(other)
    db.commit()
    response = session.patch(f"/v1/users/{other.id}", json={"is_active": False})
    assert response.status_code == 409 and "at least one" in response.json()["error"]["message"]


def test_users_of_other_tenants_cannot_be_touched(client, admin, make_user, make_tenant):
    stranger = make_user("stranger@elsewhere.test", make_tenant("Elsewhere"))
    session = sign_in(client, admin.email)
    assert session.patch(f"/v1/users/{stranger.id}", json={"role": "admin"}).status_code == 404


def test_password_change_requires_the_current_password(client, make_user, login):
    session = login(make_user())
    response = session.post(
        "/v1/auth/password", json={"current_password": "wrong", "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 400


@pytest.mark.parametrize("new_password", ["short", PASSWORD])
def test_password_change_enforces_length_and_novelty(client, make_user, login, new_password):
    session = login(make_user())
    response = session.post(
        "/v1/auth/password", json={"current_password": PASSWORD, "new_password": new_password}
    )
    assert response.status_code == 422


def test_password_change_keeps_this_session_and_ends_the_others(client, make_user, db):
    user = make_user()
    here, elsewhere = sign_in(client, user.email), sign_in(client, user.email)
    response = here.post(
        "/v1/auth/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 204
    assert here.get("/v1/auth/me").status_code == 200
    assert elsewhere.get("/v1/auth/me").status_code == 401
    assert db.scalar(select(func.count()).select_from(UserSession)) == 1
    sign_in(client, user.email, NEW_PASSWORD)
    old = TestClient(client.app).post(
        "/v1/auth/login", json={"email": user.email, "password": PASSWORD}
    )
    assert old.status_code == 401


def test_password_changes_are_rate_limited(client, make_user, login, monkeypatch):
    monkeypatch.setattr(get_settings(), "password_changes_per_hour", 2)
    session = login(make_user())
    body = {"current_password": "wrong", "new_password": NEW_PASSWORD}
    codes = [session.post("/v1/auth/password", json=body).status_code for _ in range(3)]
    assert codes == [400, 400, 429]
