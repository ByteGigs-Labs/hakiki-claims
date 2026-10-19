from sqlalchemy import select

from api.db.models import AuditLog, ClaimChecked
from api.security import Principal, Role
from api.services.checks import record_check
from reasoner import audit


def principal(user) -> Principal:
    return Principal(user.id, user.tenant_id, user.name, "Mercy Hospital", Role.CLERK)


def test_record_check_stores_claim_and_audit_entry(db, make_user, claim, result):
    actor = principal(make_user())
    stored = record_check(db, actor, claim, result)
    db.commit()
    row = db.scalar(select(ClaimChecked))
    assert (row.verdict, row.has_preauth, row.patient_token) == ("WILL_FAIL", False, "pat-abc")
    assert float(row.revenue_at_risk_kes) == 45000
    assert row.trace_hash == stored["trace_hash"]
    assert db.scalar(select(AuditLog)).entry_hash is not None


def test_record_check_returns_result_with_hashes(db, make_user, claim, result):
    stored = record_check(db, principal(make_user()), claim, result)
    assert stored["prev_hash"] == audit.GENESIS_HASH
    assert stored["trace_hash"].startswith("sha256:")
    assert {key: stored[key] for key in result} == result


def test_same_claim_checked_twice_has_identical_trace_hash(db, make_user, claim, result):
    actor = principal(make_user())
    first = record_check(db, actor, claim, result)
    second = record_check(db, actor, claim, result)
    assert first["trace_hash"] == second["trace_hash"]
    assert second["prev_hash"] != first["prev_hash"]


def test_preauth_reference_is_stored_as_a_flag_only(db, make_user, claim, result):
    record_check(db, principal(make_user()), {**claim, "preauth_ref": "PA-99812"}, result)
    db.commit()
    assert db.scalar(select(ClaimChecked)).has_preauth is True


def test_chain_stays_valid_after_checks(db, make_user, claim, result):
    actor = principal(make_user())
    for _ in range(3):
        record_check(db, actor, claim, result)
    db.commit()
    assert audit.verify_chain(db, actor.tenant_id).entries == 3
