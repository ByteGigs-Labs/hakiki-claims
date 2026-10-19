from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.config import get_settings
from api.db.session import get_db
from api.ratelimit import (
    clear_login_failures,
    ensure_account_not_locked,
    login_ip_limit,
    record_login_failure,
)
from api.security import Principal, authenticate, create_session, current_principal, end_session

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


class Identity(BaseModel):
    id: UUID
    name: str
    facility: str
    role: str


def _identity(principal: Principal) -> Identity:
    return Identity(
        id=principal.user_id,
        name=principal.name,
        facility=principal.facility,
        role=principal.role.value,
    )


def _cookie_options() -> dict:
    return {
        "path": "/",
        "httponly": True,
        "secure": get_settings().cookie_secure,
        "samesite": "strict",
    }


@router.post("/login", dependencies=[Depends(login_ip_limit)])
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> Identity:
    ensure_account_not_locked(body.email)
    user = authenticate(db, body.email, body.password)
    if not user:
        record_login_failure(body.email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    clear_login_failures(body.email)
    settings = get_settings()
    response.set_cookie(
        settings.cookie_name,
        create_session(db, user),
        max_age=settings.session_ttl_hours * 3600,
        **_cookie_options(),
    )
    return Identity(id=user.id, name=user.name, facility=user.tenant.name, role=user.role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    name = get_settings().cookie_name
    if token := request.cookies.get(name):
        end_session(db, token)
    response.delete_cookie(name, **_cookie_options())


@router.get("/me")
def me(principal: Principal = Depends(current_principal)) -> Identity:
    return _identity(principal)
