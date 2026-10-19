from sqlalchemy import func, select

from api.db.models import AuditLog, ClaimChecked
from ingest.pseudonymise import patient_token
from reasoner import audit

BODY = {
    "claim_ref": "clm-104",
    "patient_token": "pat-77",
    "facility_id": "fac-12",
    "service_code": "svc-CS-01",
    "fund": "SHIF",
    "date_of_service": "2026-10-14",
    "amount_kes": 45000,
    "member_status": "active",
}


def test_requires_authentication(client):
    assert client.post("/v1/claims/check", json=BODY).status_code == 401


def test_returns_the_contract_shape(client, make_user, login):
    result = login(make_user()).post("/v1/claims/check", json=BODY).json()
    assert result["claim"] == "clm-104" and result["verdict"] == "WILL_FAIL"
    assert result["truth_value"] == {"strength": 0.95, "confidence": 0.92}
    assert result["revenue_at_risk_kes"] == 45000
    assert result["trace_hash"].startswith("sha256:")
    assert result["prev_hash"] == audit.GENESIS_HASH
    assert result["fixes"][0]["flips_to"] == "PASS"


def test_same_claim_twice_gives_identical_trace_hash_and_a_chained_prev_hash(
    client, make_user, login
):
    session = login(make_user())
    first = session.post("/v1/claims/check", json=BODY).json()
    second = session.post("/v1/claims/check", json=BODY).json()
    assert first["trace_hash"] == second["trace_hash"]
    assert second["prev_hash"] != first["prev_hash"]


def test_fixed_claim_flips_to_pass_through_the_api(client, make_user, login):
    session = login(make_user())
    fix = session.post("/v1/claims/check", json=BODY).json()["fixes"][0]
    fixed = session.post("/v1/claims/check", json={**BODY, **fix["patch"]}).json()
    assert fixed["verdict"] == "PASS" and fixed["revenue_at_risk_kes"] == 0


def test_every_check_is_stored_and_the_chain_verifies(client, make_user, login, db):
    session = login(make_user())
    session.post("/v1/claims/check", json=BODY)
    session.post("/v1/claims/check", json={**BODY, "preauth_ref": "PA-1001"})
    assert db.scalar(select(func.count()).select_from(ClaimChecked)) == 2
    assert session.get("/v1/audit/verify").json() == {
        "valid": True,
        "entries": 2,
        "head_hash": db.scalars(select(AuditLog).order_by(AuditLog.seq.desc())).first().entry_hash,
        "broken_at": None,
    }


def test_raw_patient_id_is_tokenised_and_never_stored(client, make_user, login, db):
    body = {k: v for k, v in BODY.items() if k != "patient_token"} | {"patient_id": "A1234567"}
    login(make_user()).post("/v1/claims/check", json=body)
    stored = db.scalar(select(ClaimChecked))
    assert stored.patient_token == patient_token("A1234567")
    audit_text = str(db.scalar(select(AuditLog)).payload)
    assert "A1234567" not in audit_text and "A1234567" not in stored.patient_token


def test_duplicate_detection_uses_the_tenants_own_history(client, make_user, make_tenant, login):
    session = login(make_user("a@a.test", make_tenant("A")))
    session.post(
        "/v1/claims/check",
        json={**BODY, "claim_ref": "clm-1", "service_code": "svc-OPD-01", "amount_kes": 700},
    )
    duplicate = session.post(
        "/v1/claims/check",
        json={**BODY, "claim_ref": "clm-2", "service_code": "svc-OPD-01", "amount_kes": 700},
    ).json()
    assert duplicate["verdict"] == "WILL_FAIL"
    assert any(s["rule"].startswith("R8") and s["result"] == "fail" for s in duplicate["trace"])


def test_other_tenants_history_is_never_used_for_duplicates(client, make_user, make_tenant, login):
    body = {**BODY, "service_code": "svc-OPD-01", "amount_kes": 700}
    login(make_user("a@a.test", make_tenant("A"))).post(
        "/v1/claims/check", json={**body, "claim_ref": "clm-1"}
    )
    client.cookies.clear()
    other = (
        login(make_user("b@b.test", make_tenant("B")))
        .post("/v1/claims/check", json={**body, "claim_ref": "clm-2"})
        .json()
    )
    assert other["verdict"] == "PASS"


def test_citation_endpoint_returns_the_source_for_a_rule(client, make_user, login):
    session = login(make_user())
    citation = session.get("/v1/citations/R3").json()
    assert citation["rule"] == "R3" and citation["document"].startswith("Social Health Insurance")
    assert citation["verified"] is False
    assert session.get("/v1/citations/R99").status_code == 404
    client.cookies.clear()
    assert client.get("/v1/citations/R3").status_code == 401
