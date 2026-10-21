import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from api.config import get_settings
from api.db.models import ApiKey, ClaimChecked, User
from api.routes.api_keys import MAX_ACTIVE_KEYS
from api.security import Role

from .conftest import PASSWORD
from .test_batch import HEADER, row, upload
from .test_check_api import BODY


@pytest.fixture
def issue(client, make_user):
    count = 0

    def create(tenant=None, name="Billing system") -> tuple[str, dict, TestClient]:
        nonlocal count
        count += 1
        admin = make_user(f"admin{count}@mercy.test", tenant, Role.ADMIN)
        session = TestClient(client.app)
        session.post("/v1/auth/login", json={"email": admin.email, "password": PASSWORD})
        created = session.post("/v1/api-keys", json={"name": name}).json()
        return created["key"], created, session

    return create


def bearer(client, key: str) -> TestClient:
    return TestClient(client.app, headers={"Authorization": f"Bearer {key}"})


def test_a_key_is_shown_once_and_only_its_hash_is_stored(issue, db):
    key, created, _ = issue()
    assert key.startswith("hk_") and created["prefix"] == key[3:11] and len(key) == 44
    stored = db.scalars(select(ApiKey)).one()
    assert stored.key_hash == hashlib.sha256(key.encode()).hexdigest()
    columns = [str(getattr(stored, column.name)) for column in ApiKey.__table__.columns]
    assert all(key not in value for value in columns)


def test_listing_never_repeats_the_key(issue):
    key, created, admin = issue()
    listing = admin.get("/v1/api-keys")
    assert listing.status_code == 200 and key not in listing.text
    assert listing.json()[0]["prefix"] == created["prefix"] and "key" not in listing.json()[0]


def test_a_key_checks_a_claim_and_fetches_its_explanation(client, issue):
    key, _, _ = issue()
    caller = bearer(client, key)
    response = caller.post("/v1/claims/check", json=BODY)
    assert response.status_code == 200 and response.json()["verdict"] == "WILL_FAIL"
    explained = caller.get(f"/v1/claims/{response.json()['trace_hash']}/explanation")
    assert explained.status_code == 200


def test_a_key_uploads_a_batch_and_reads_the_result(client, issue):
    key, _, _ = issue()
    caller = bearer(client, key)
    accepted = upload(caller, HEADER + row("a") + row("b", patient="PT-2"))
    assert accepted.status_code == 202
    batch_id = accepted.json()["id"]
    assert caller.get(f"/v1/claims/batch/{batch_id}").json()["status"] == "done"
    assert caller.get(f"/v1/claims/batch/{batch_id}/rows").headers["X-Total-Count"] == "2"


@pytest.mark.parametrize("header", ["Bearer hk_deadbeef_nope", "Bearer ", "Bearer", "Basic abc"])
def test_bad_credentials_are_rejected(client, header):
    response = client.post("/v1/claims/check", json=BODY, headers={"Authorization": header})
    assert response.status_code == 401


def test_a_revoked_key_stops_working(client, issue):
    key, created, admin = issue()
    assert bearer(client, key).post("/v1/claims/check", json=BODY).status_code == 200
    assert admin.delete(f"/v1/api-keys/{created['id']}").status_code == 204
    assert bearer(client, key).post("/v1/claims/check", json=BODY).status_code == 401
    assert admin.delete(f"/v1/api-keys/{created['id']}").status_code == 204


def test_a_deactivated_creator_disables_their_keys(client, issue, db):
    key, _, _ = issue()
    db.scalars(select(User)).one().is_active = False
    db.commit()
    assert bearer(client, key).post("/v1/claims/check", json=BODY).status_code == 401


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/v1/claims"),
        ("get", "/v1/auth/me"),
        ("get", "/v1/api-keys"),
        ("post", "/v1/api-keys"),
        ("get", "/v1/audit/verify"),
        ("get", "/v1/reports/overview"),
    ],
)
def test_a_key_cannot_reach_session_only_endpoints(client, issue, method, path):
    key, _, _ = issue()
    response = getattr(bearer(client, key), method)(path)
    assert response.status_code == 401


def test_only_admins_manage_keys(make_user, login):
    clerk = login(make_user("clerk@mercy.test", role=Role.CLERK))
    assert clerk.post("/v1/api-keys", json={"name": "x"}).status_code == 403
    assert clerk.get("/v1/api-keys").status_code == 403


def test_keys_are_isolated_between_tenants(issue, make_tenant):
    _, mine, admin = issue()
    _, theirs, _ = issue(make_tenant("Other Hospital"), name="Other")
    assert [item["id"] for item in admin.get("/v1/api-keys").json()] == [mine["id"]]
    assert admin.delete(f"/v1/api-keys/{theirs['id']}").status_code == 404


def test_checks_are_recorded_against_the_keys_tenant(client, issue, make_tenant, db):
    other = make_tenant("Other Hospital")
    key, _, _ = issue(other, name="Other")
    bearer(client, key).post("/v1/claims/check", json=BODY)
    assert db.scalars(select(ClaimChecked.tenant_id)).one() == other.id


def test_each_key_has_its_own_rate_limit(client, issue, monkeypatch):
    monkeypatch.setattr(get_settings(), "check_per_minute", 2)
    first, _, _ = issue(name="One")
    second, _, _ = issue(name="Two")
    statuses = [
        bearer(client, first).post("/v1/claims/check", json=BODY).status_code for _ in range(3)
    ]
    assert statuses == [200, 200, 429]
    assert bearer(client, second).post("/v1/claims/check", json=BODY).status_code == 200


def test_key_count_is_capped(issue):
    _, _, admin = issue()
    for index in range(MAX_ACTIVE_KEYS - 1):
        assert admin.post("/v1/api-keys", json={"name": f"k{index}"}).status_code == 201
    assert admin.post("/v1/api-keys", json={"name": "one too many"}).status_code == 409


def test_last_used_is_recorded(client, issue, db):
    key, _, _ = issue()
    assert db.scalars(select(ApiKey)).one().last_used_at is None
    bearer(client, key).post("/v1/claims/check", json=BODY)
    db.expire_all()
    assert db.scalars(select(ApiKey)).one().last_used_at is not None
