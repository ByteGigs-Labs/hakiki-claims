import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from api.config import get_settings
from api.db.models import ApiKey, Tenant, User, UserSession
from api.db.session import get_db

MIN_PASSWORD_LENGTH = 10
KEY_TOUCH_INTERVAL = timedelta(minutes=1)

_hasher = PasswordHasher()
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


class Role(StrEnum):
    CLERK = "clerk"
    FINANCE_MANAGER = "finance_manager"
    ADMIN = "admin"


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    tenant_id: UUID
    name: str
    facility: str
    role: Role
    api_key_id: UUID | None = None


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    password_ok = verify_password(user.password_hash if user else _DUMMY_HASH, password)
    return user if user and user.is_active and password_ok else None


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(UTC) + timedelta(hours=get_settings().session_ttl_hours)
    db.add(UserSession(user_id=user.id, token_hash=_token_hash(token), expires_at=expires))
    db.commit()
    return token


def end_session(db: Session, token: str) -> None:
    session = db.scalar(select(UserSession).where(UserSession.token_hash == _token_hash(token)))
    if session:
        db.delete(session)
        db.commit()


def current_principal(request: Request, db: Session = Depends(get_db)) -> Principal:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    token = request.cookies.get(get_settings().cookie_name)
    if not token:
        raise unauthorized
    row = db.execute(
        select(User, Tenant)
        .join(UserSession, UserSession.user_id == User.id)
        .join(Tenant, Tenant.id == User.tenant_id)
        .where(
            UserSession.token_hash == _token_hash(token),
            UserSession.expires_at > datetime.now(UTC),
            User.is_active.is_(True),
        )
    ).first()
    if not row:
        raise unauthorized
    user, tenant = row
    return Principal(user.id, tenant.id, user.name, tenant.name, Role(user.role))


def require_roles(*roles: Role) -> Callable[[Principal], Principal]:
    def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return principal

    return dependency


def create_api_key(db: Session, principal: Principal, name: str) -> tuple[ApiKey, str]:
    prefix = secrets.token_hex(4)
    key = f"hk_{prefix}_{secrets.token_urlsafe(24)}"
    row = ApiKey(
        tenant_id=principal.tenant_id,
        created_by=principal.user_id,
        name=name,
        prefix=prefix,
        key_hash=_token_hash(key),
    )
    db.add(row)
    db.commit()
    return row, key


def _principal_from_key(db: Session, key: str) -> Principal | None:
    found = db.execute(
        select(ApiKey, User, Tenant)
        .join(User, User.id == ApiKey.created_by)
        .join(Tenant, Tenant.id == ApiKey.tenant_id)
        .where(
            ApiKey.key_hash == _token_hash(key),
            ApiKey.revoked_at.is_(None),
            User.is_active.is_(True),
        )
    ).first()
    if not found:
        return None
    api_key, user, tenant = found
    now = datetime.now(UTC)
    if api_key.last_used_at is None or now - api_key.last_used_at > KEY_TOUCH_INTERVAL:
        api_key.last_used_at = now
        db.commit()
    return Principal(user.id, tenant.id, user.name, tenant.name, Role.CLERK, api_key.id)


def current_principal_or_key(request: Request, db: Session = Depends(get_db)) -> Principal:
    scheme, _, credential = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer":
        return current_principal(request, db)
    principal = _principal_from_key(db, credential.strip()) if credential else None
    if not principal:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return principal


def change_password(db: Session, user: User, new_password: str, keep_token: str | None) -> None:
    user.password_hash = hash_password(new_password)
    others = delete(UserSession).where(UserSession.user_id == user.id)
    if keep_token:
        others = others.where(UserSession.token_hash != _token_hash(keep_token))
    db.execute(others)
    db.commit()
