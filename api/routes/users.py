from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.db.models import User, UserSession
from api.db.session import get_db
from api.security import MIN_PASSWORD_LENGTH, Principal, Role, hash_password, require_roles

router = APIRouter(prefix="/v1/users", tags=["users"])

Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    role: Role
    is_active: bool
    created_at: datetime


class NewUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    email: Email
    role: Role
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=256)


class UserChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role | None = None
    is_active: bool | None = None


def _find(db: Session, principal: Principal, user_id: UUID) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.tenant_id == principal.tenant_id))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


def _other_active_admins(db: Session, user: User) -> int:
    return db.scalar(
        select(func.count())
        .select_from(User)
        .where(
            User.tenant_id == user.tenant_id,
            User.role == Role.ADMIN.value,
            User.is_active.is_(True),
            User.id != user.id,
        )
    )


@router.get("")
def list_users(
    principal: Principal = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)
) -> list[UserOut]:
    users = db.scalars(
        select(User)
        .where(User.tenant_id == principal.tenant_id)
        .order_by(User.created_at, User.name)
    )
    return [UserOut.model_validate(user) for user in users]


@router.post("", status_code=status.HTTP_201_CREATED)
def add_user(
    body: NewUser,
    principal: Principal = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserOut:
    user = User(
        tenant_id=principal.tenant_id,
        email=body.email,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        role=body.role.value,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered") from error
    return UserOut.model_validate(user)


@router.patch("/{user_id}")
def change_user(
    user_id: UUID,
    body: UserChange,
    principal: Principal = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserOut:
    user = _find(db, principal, user_id)
    role = body.role.value if body.role else user.role
    active = user.is_active if body.is_active is None else body.is_active
    if user.id == principal.user_id and (role != user.role or not active):
        raise HTTPException(status.HTTP_409_CONFLICT, "You cannot demote or deactivate yourself")
    stays_admin = active and role == Role.ADMIN.value
    was_admin = user.is_active and user.role == Role.ADMIN.value
    if was_admin and not stays_admin and not _other_active_admins(db, user):
        raise HTTPException(status.HTTP_409_CONFLICT, "A facility needs at least one active admin")
    user.role, user.is_active = role, active
    if not active:
        db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.commit()
    return UserOut.model_validate(user)
