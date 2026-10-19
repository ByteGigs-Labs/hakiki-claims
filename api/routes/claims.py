from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import get_settings
from api.db.models import AuditLog
from api.db.session import get_db
from api.ratelimit import check_limit
from api.security import Principal
from api.services.checks import check_and_record
from ingest.claim_schema import ClaimInput
from narrator.service import build_completion, narrate

router = APIRouter(prefix="/v1/claims", tags=["claims"])


@router.post("/check")
def check_claim(
    body: ClaimInput,
    principal: Principal = Depends(check_limit),
    db: Session = Depends(get_db),
) -> dict:
    result = check_and_record(db, principal, body.to_claim())
    db.commit()
    return result


@router.get("/{trace_hash}/explanation")
def explain_check(
    trace_hash: str,
    language: Literal["en", "sw"] = Query("en", alias="lang"),
    principal: Principal = Depends(check_limit),
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
    narration = narrate(entry.payload, language, build_completion(get_settings()))
    return {
        "language": narration.language,
        "text": narration.text,
        "source": narration.source,
        "verdict": entry.payload["verdict"],
    }
