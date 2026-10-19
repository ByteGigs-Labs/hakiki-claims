from api.security import Principal, Role
from api.services.checks import record_check


def seed(db, user, claim, result, count: int, **overrides) -> None:
    actor = Principal(user.id, user.tenant_id, user.name, "Mercy Hospital", Role.CLERK)
    for index in range(count):
        record_check(
            db,
            actor,
            {**claim, "amount_kes": 1000 + index, **overrides},
            {**result, "claim": f"clm-{index}"},
        )
    db.commit()


def test_requires_authentication(client):
    assert client.get("/v1/claims").status_code == 401
    assert client.get("/v1/audit/verify").status_code == 401


def test_lists_rows_in_the_refine_shape(client, db, make_user, login, claim, result):
    user = make_user()
    seed(db, user, claim, result, 2)
    response = login(user).get("/v1/claims")
    row = response.json()[0]
    assert set(row) == {
        "id",
        "claim_ref",
        "service_code",
        "fund",
        "amount_kes",
        "verdict",
        "revenue_at_risk_kes",
        "trace_hash",
        "checked_at",
    }
    assert response.headers["x-total-count"] == "2"


def test_paginates_and_reports_the_total(client, db, make_user, login, claim, result):
    user = make_user()
    seed(db, user, claim, result, 5)
    response = login(user).get("/v1/claims", params={"_start": 2, "_end": 4})
    assert len(response.json()) == 2
    assert response.headers["x-total-count"] == "5"


def test_sorts_by_allowed_fields(client, db, make_user, login, claim, result):
    user = make_user()
    seed(db, user, claim, result, 3)
    session = login(user)
    ascending = [
        r["amount_kes"]
        for r in session.get("/v1/claims", params={"_sort": "amount_kes", "_order": "ASC"}).json()
    ]
    descending = [
        r["amount_kes"]
        for r in session.get("/v1/claims", params={"_sort": "amount_kes", "_order": "DESC"}).json()
    ]
    assert ascending == sorted(ascending) and descending == ascending[::-1]


def test_sort_direction_is_case_insensitive_for_refine(client, db, make_user, login, claim, result):
    user = make_user()
    seed(db, user, claim, result, 3)
    session = login(user)

    def amounts(order: str) -> list:
        response = session.get("/v1/claims", params={"_sort": "amount_kes", "_order": order})
        return [row["amount_kes"] for row in response.json()]

    assert amounts("asc") == amounts("ASC") == amounts("desc")[::-1]


def test_rejects_unlisted_sort_fields(client, make_user, login):
    session = login(make_user())
    assert session.get("/v1/claims", params={"_sort": "patient_token"}).status_code == 422
    assert session.get("/v1/claims", params={"_sort": "id; DROP TABLE users"}).status_code == 422
    assert session.get("/v1/claims", params={"_order": "sideways"}).status_code == 422


def test_rejects_invalid_ranges(client, make_user, login):
    session = login(make_user())
    assert session.get("/v1/claims", params={"_start": 5, "_end": 5}).status_code == 422
    assert session.get("/v1/claims", params={"_start": 0, "_end": 101}).status_code == 422
    assert session.get("/v1/claims", params={"_start": -1}).status_code == 422


def test_other_tenants_claims_are_invisible(
    client, db, make_user, make_tenant, login, claim, result
):
    mine, theirs = (
        make_user("me@a.test", make_tenant("A")),
        make_user("you@b.test", make_tenant("B")),
    )
    seed(db, mine, claim, result, 2)
    seed(db, theirs, claim, result, 4)
    response = login(mine).get("/v1/claims")
    assert len(response.json()) == 2 and response.headers["x-total-count"] == "2"


def test_audit_verify_reports_a_valid_chain(client, db, make_user, login, claim, result):
    user = make_user()
    seed(db, user, claim, result, 3)
    body = login(user).get("/v1/audit/verify").json()
    assert (body["valid"], body["entries"], body["broken_at"]) == (True, 3, None)


def test_audit_verify_only_covers_own_tenant(
    client, db, make_user, make_tenant, login, claim, result
):
    mine, theirs = (
        make_user("me@a.test", make_tenant("A")),
        make_user("you@b.test", make_tenant("B")),
    )
    seed(db, theirs, claim, result, 4)
    assert login(mine).get("/v1/audit/verify").json()["entries"] == 0
