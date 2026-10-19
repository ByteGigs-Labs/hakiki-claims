from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
