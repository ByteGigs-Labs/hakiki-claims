import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from api.db.models import AuditLog

GENESIS_HASH = "sha256:" + "0" * 64


@dataclass(frozen=True)
class ChainStatus:
    valid: bool
    entries: int
    head_hash: str
    broken_at: int | None = None


def _digest(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def trace_hash(payload: dict) -> str:
    return _digest(payload)


def entry_hash(tenant_id: UUID, seq: int, prev_hash: str, trace: str) -> str:
    return _digest({"tenant": str(tenant_id), "seq": seq, "prev": prev_hash, "trace": trace})


def _lock_chain(session: Session, tenant_id: UUID) -> None:
    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant, 0))"),
        {"tenant": str(tenant_id)},
    )


def append(
    session: Session, tenant_id: UUID, claim_ref: str, rulebook_version: str, payload: dict
) -> AuditLog:
    _lock_chain(session, tenant_id)
    head = session.scalar(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.seq.desc())
        .limit(1)
    )
    seq = head.seq + 1 if head else 1
    prev = head.entry_hash if head else GENESIS_HASH
    trace = trace_hash(payload)
    row = AuditLog(
        tenant_id=tenant_id,
        seq=seq,
        claim_ref=claim_ref,
        rulebook_version=rulebook_version,
        payload=payload,
        trace_hash=trace,
        prev_hash=prev,
        entry_hash=entry_hash(tenant_id, seq, prev, trace),
    )
    session.add(row)
    session.flush()
    return row


def verify_chain(session: Session, tenant_id: UUID) -> ChainStatus:
    rows = session.scalars(
        select(AuditLog).where(AuditLog.tenant_id == tenant_id).order_by(AuditLog.seq)
    )
    prev = GENESIS_HASH
    count = 0
    for expected_seq, row in enumerate(rows, start=1):
        trace = trace_hash(row.payload)
        intact = (
            row.seq == expected_seq
            and row.prev_hash == prev
            and row.trace_hash == trace
            and row.entry_hash == entry_hash(tenant_id, row.seq, prev, trace)
        )
        if not intact:
            return ChainStatus(False, count, prev, broken_at=expected_seq)
        prev = row.entry_hash
        count = expected_seq
    return ChainStatus(True, count, prev)
