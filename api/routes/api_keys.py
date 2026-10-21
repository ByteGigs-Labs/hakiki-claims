from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.db.models import ApiKey
from api.db.session import get_db
from api.security import Principal, Role, create_api_key, require_roles

router = APIRouter(prefix="/v1/api-keys", tags=["api-keys"])

MAX_ACTIVE_KEYS = 20


class NewKey(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)


class KeySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    prefix: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class CreatedKey(KeySummary):
    key: str


def _active(principal: Principal):
    return (ApiKey.tenant_id == principal.tenant_id, ApiKey.revoked_at.is_(None))


@router.post("", status_code=status.HTTP_201_CREATED)
def issue_key(
    body: NewKey,
    principal: Principal = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> CreatedKey:
    active = db.scalar(select(func.count()).select_from(ApiKey).where(*_active(principal)))
    if active >= MAX_ACTIVE_KEYS:
        raise HTTPException(status.HTTP_409_CONFLICT, "Revoke an unused key first")
    row, key = create_api_key(db, principal, body.name.strip())
    return CreatedKey(**KeySummary.model_validate(row).model_dump(), key=key)


@router.get("")
def list_keys(
    principal: Principal = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)
) -> list[KeySummary]:
    rows = db.scalars(
        select(ApiKey).where(ApiKey.tenant_id == principal.tenant_id).order_by(ApiKey.created_at)
    )
    return [KeySummary.model_validate(row) for row in rows]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_key(
    key_id: UUID,
    principal: Principal = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> Response:
    row = db.scalar(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.tenant_id == principal.tenant_id)
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Key not found")
    if row.revoked_at is None:
        row.revoked_at = func.now()
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
