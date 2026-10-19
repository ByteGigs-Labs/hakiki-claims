import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from reasoner import audit


@pytest.fixture
def tenant(make_tenant):
    return make_tenant()


def payload(claim: str = "clm-1", **extra) -> dict:
    return {"claim": claim, "verdict": "PASS", "trace": [{"step": 1}], **extra}


def test_trace_hash_ignores_key_order():
    assert audit.trace_hash({"a": 1, "b": [2, 3]}) == audit.trace_hash({"b": [2, 3], "a": 1})


def test_trace_hash_changes_with_content():
    assert audit.trace_hash(payload("clm-1")) != audit.trace_hash(payload("clm-2"))


def test_first_entry_links_to_genesis(db, tenant):
    entry = audit.append(db, tenant.id, "clm-1", "v1", payload())
    assert (entry.seq, entry.prev_hash) == (1, audit.GENESIS_HASH)


def test_entries_chain_and_verify(db, tenant):
    first = audit.append(db, tenant.id, "clm-1", "v1", payload("clm-1"))
    second = audit.append(db, tenant.id, "clm-2", "v1", payload("clm-2"))
    db.commit()
    status = audit.verify_chain(db, tenant.id)
    assert second.prev_hash == first.entry_hash
    assert status == audit.ChainStatus(True, 2, second.entry_hash)


def test_same_payload_gives_same_trace_hash_but_new_entry_hash(db, tenant):
    first = audit.append(db, tenant.id, "clm-1", "v1", payload())
    second = audit.append(db, tenant.id, "clm-1", "v1", payload())
    assert first.trace_hash == second.trace_hash
    assert first.entry_hash != second.entry_hash


def test_empty_chain_is_valid(db, tenant):
    assert audit.verify_chain(db, tenant.id) == audit.ChainStatus(True, 0, audit.GENESIS_HASH)


def test_hash_survives_jsonb_round_trip(db, engine, tenant):
    audit.append(db, tenant.id, "clm-1", "v1", payload(truth_value={"strength": 0.95}, kes=45000.5))
    db.commit()
    with Session(engine) as fresh:
        assert audit.verify_chain(fresh, tenant.id).valid


def test_update_is_rejected_by_the_database(db, tenant):
    audit.append(db, tenant.id, "clm-1", "v1", payload())
    db.commit()
    with pytest.raises(DBAPIError, match="append-only"):
        db.execute(text("UPDATE audit_log SET claim_ref = 'x'"))


def test_delete_is_rejected_by_the_database(db, tenant):
    audit.append(db, tenant.id, "clm-1", "v1", payload())
    db.commit()
    with pytest.raises(DBAPIError, match="append-only"):
        db.execute(text("DELETE FROM audit_log"))


def tamper(db, sql: str, **params) -> None:
    db.execute(text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_immutable"))
    db.execute(text(sql), params)
    db.execute(text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_immutable"))
    db.commit()


def test_modified_payload_is_detected(db, tenant):
    for index in range(3):
        audit.append(db, tenant.id, f"clm-{index}", "v1", payload(f"clm-{index}"))
    db.commit()
    tamper(
        db, """UPDATE audit_log SET payload = '{"claim":"clm-1","verdict":"FAIL"}' WHERE seq = 2"""
    )
    status = audit.verify_chain(db, tenant.id)
    assert (status.valid, status.broken_at) == (False, 2)


def test_deleted_entry_is_detected(db, tenant):
    for index in range(3):
        audit.append(db, tenant.id, f"clm-{index}", "v1", payload(f"clm-{index}"))
    db.commit()
    tamper(db, "DELETE FROM audit_log WHERE seq = 2")
    status = audit.verify_chain(db, tenant.id)
    assert (status.valid, status.broken_at) == (False, 2)


def test_rewritten_link_is_detected(db, tenant):
    for index in range(2):
        audit.append(db, tenant.id, f"clm-{index}", "v1", payload(f"clm-{index}"))
    db.commit()
    tamper(
        db,
        "UPDATE audit_log SET prev_hash = :genesis WHERE seq = 2",
        genesis=audit.GENESIS_HASH,
    )
    assert audit.verify_chain(db, tenant.id).broken_at == 2


def test_tenant_chains_are_independent(db, make_tenant):
    one, two = make_tenant("One"), make_tenant("Two")
    audit.append(db, one.id, "clm-1", "v1", payload())
    entry = audit.append(db, two.id, "clm-1", "v1", payload())
    assert (entry.seq, entry.prev_hash) == (1, audit.GENESIS_HASH)
