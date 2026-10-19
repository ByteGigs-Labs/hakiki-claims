from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import AuditLog
from api.db.session import get_db
from api.security import Principal, current_principal
from reasoner import audit

router = APIRouter(prefix="/v1/audit", tags=["audit"])


class ChainResponse(BaseModel):
    valid: bool
    entries: int
    head_hash: str
    broken_at: int | None


@router.get("/verify")
def verify(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> ChainResponse:
    status = audit.verify_chain(db, principal.tenant_id)
    return ChainResponse(
        valid=status.valid,
        entries=status.entries,
        head_hash=status.head_hash,
        broken_at=status.broken_at,
    )


@router.get("/entries/{trace_hash}")
def stored_check(
    trace_hash: str,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> dict:
    entry = db.scalar(
        select(AuditLog)
        .where(AuditLog.tenant_id == principal.tenant_id, AuditLog.trace_hash == trace_hash)
        .order_by(AuditLog.seq.desc())
        .limit(1)
    )
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Check not found")
    return {**entry.payload, "trace_hash": entry.trace_hash, "prev_hash": entry.prev_hash}
