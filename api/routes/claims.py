from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.ratelimit import check_limit
from api.security import Principal
from api.services.checks import check_and_record
from ingest.claim_schema import ClaimInput

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
