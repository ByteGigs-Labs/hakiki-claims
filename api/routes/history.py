from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.db.models import ClaimChecked
from api.db.session import get_db
from api.security import Principal, current_principal

router = APIRouter(prefix="/v1/claims", tags=["claims"])

MAX_PAGE_SIZE = 100
SortField = Literal["checked_at", "amount_kes", "verdict", "service_code", "fund"]


class ClaimRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_ref: str
    service_code: str
    fund: str
    amount_kes: Decimal
    verdict: str
    revenue_at_risk_kes: Decimal
    trace_hash: str
    checked_at: datetime


@router.get("")
def list_claims(
    response: Response,
    start: int = Query(0, alias="_start", ge=0),
    end: int = Query(10, alias="_end", ge=1),
    sort: SortField = Query("checked_at", alias="_sort"),
    order: Literal["ASC", "DESC"] = Query("DESC", alias="_order"),
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> list[ClaimRow]:
    if end <= start or end - start > MAX_PAGE_SIZE:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid page range")
    scope = ClaimChecked.tenant_id == principal.tenant_id
    column = getattr(ClaimChecked, sort)
    rows = db.scalars(
        select(ClaimChecked)
        .where(scope)
        .order_by(column.asc() if order == "ASC" else column.desc(), ClaimChecked.id)
        .offset(start)
        .limit(end - start)
    )
    response.headers["X-Total-Count"] = str(
        db.scalar(select(func.count()).select_from(ClaimChecked).where(scope))
    )
    return [ClaimRow.model_validate(row) for row in rows]
