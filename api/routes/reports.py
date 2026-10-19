from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.schemas import Overview
from api.security import Principal, Role, require_roles
from api.services.reports import overview

router = APIRouter(prefix="/v1/reports", tags=["reports"])


@router.get("/overview", response_model=Overview)
def get_overview(
    days: int = Query(30, ge=1, le=365),
    principal: Principal = Depends(require_roles(Role.FINANCE_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    return overview(db, principal.tenant_id, days)
