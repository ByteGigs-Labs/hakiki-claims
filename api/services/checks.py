from uuid import UUID

from sqlalchemy.orm import Session

from api.db.models import ClaimChecked
from api.security import Principal
from reasoner import audit

HASH_FIELDS = ("trace_hash", "prev_hash")


def record_check(
    db: Session,
    principal: Principal,
    claim: dict,
    result: dict,
    batch_id: UUID | None = None,
) -> dict:
    payload = {key: value for key, value in result.items() if key not in HASH_FIELDS}
    entry = audit.append(
        db, principal.tenant_id, payload["claim"], payload["rulebook_version"], payload
    )
    db.add(
        ClaimChecked(
            tenant_id=principal.tenant_id,
            user_id=principal.user_id,
            batch_id=batch_id,
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
