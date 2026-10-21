from collections.abc import Collection
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from api.db.models import ClaimChecked
from api.security import Principal
from reasoner import audit, engine

HASH_FIELDS = ("trace_hash", "prev_hash")


def record_check(
    db: Session,
    principal: Principal,
    claim: dict,
    result: dict,
    batch_id: UUID | None = None,
    row_number: int | None = None,
    checked_at: datetime | None = None,
) -> dict:
    payload = {key: value for key, value in result.items() if key not in HASH_FIELDS}
    entry = audit.append(
        db, principal.tenant_id, payload["claim"], payload["rulebook_version"], payload
    )
    when = {"checked_at": checked_at} if checked_at else {}
    db.add(
        ClaimChecked(
            **when,
            tenant_id=principal.tenant_id,
            user_id=principal.user_id,
            batch_id=batch_id,
            row_number=row_number,
            failing_rules=[
                step["rule"].split("-")[0]
                for step in payload["trace"]
                if step["result"] in {"fail", "warn"}
            ],
            claim_ref=claim["claim_ref"],
            patient_token=claim["patient_token"],
            facility_id=claim["facility_id"],
            service_code=claim["service_code"],
            fund=claim["fund"],
            date_of_service=claim["date_of_service"],
            amount_kes=claim["amount_kes"],
            has_preauth=bool(claim.get("preauth_ref")),
            icd_code=claim.get("icd_code"),
            verdict=payload["verdict"],
            strength=payload["truth_value"]["strength"],
            confidence=payload["truth_value"]["confidence"],
            revenue_at_risk_kes=payload["revenue_at_risk_kes"],
            rulebook_version=payload["rulebook_version"],
            trace_hash=entry.trace_hash,
            audit_id=entry.id,
        )
    )
    db.flush()
    return {**payload, "trace_hash": entry.trace_hash, "prev_hash": entry.prev_hash}


def prior_summary(claim: dict) -> dict:
    return {
        "claim_ref": claim["claim_ref"],
        "patient_token": claim["patient_token"],
        "service_code": claim["service_code"],
        "date_of_service": claim["date_of_service"],
    }


def patient_history(
    db: Session, principal: Principal, tokens: Collection[str]
) -> dict[str, dict[str, dict]]:
    latest = (
        select(
            ClaimChecked.claim_ref,
            ClaimChecked.patient_token,
            ClaimChecked.service_code,
            ClaimChecked.date_of_service,
        )
        .where(
            ClaimChecked.tenant_id == principal.tenant_id,
            ClaimChecked.patient_token.in_(tokens),
        )
        .ext(distinct_on(ClaimChecked.patient_token, ClaimChecked.claim_ref))
        .order_by(
            ClaimChecked.patient_token, ClaimChecked.claim_ref, ClaimChecked.checked_at.desc()
        )
    )
    history: dict[str, dict[str, dict]] = {token: {} for token in tokens}
    for row in db.execute(latest):
        history[row.patient_token][row.claim_ref] = prior_summary(
            {**row._asdict(), "date_of_service": row.date_of_service.isoformat()}
        )
    return history


def prior_claims(db: Session, principal: Principal, claim: dict) -> list[dict]:
    history = patient_history(db, principal, [claim["patient_token"]])[claim["patient_token"]]
    return [prior for ref, prior in history.items() if ref != claim["claim_ref"]]


def check_and_record(
    db: Session,
    principal: Principal,
    claim: dict,
    batch_id: UUID | None = None,
    row_number: int | None = None,
    checked_at: datetime | None = None,
) -> dict:
    result = engine.check(claim, prior_claims(db, principal, claim))
    return record_check(db, principal, claim, result, batch_id, row_number, checked_at)
