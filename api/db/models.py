import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = _created_at()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="clerk")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _created_at()

    tenant: Mapped[Tenant] = relationship()


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()

    user: Mapped[User] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (UniqueConstraint("tenant_id", "seq"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    claim_ref: Mapped[str] = mapped_column(String(100))
    rulebook_version: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSONB)
    trace_hash: Mapped[str] = mapped_column(String(71))
    prev_hash: Mapped[str] = mapped_column(String(71))
    entry_hash: Mapped[str] = mapped_column(String(71))
    created_at: Mapped[datetime] = _created_at()


class ClaimChecked(Base):
    __tablename__ = "claims_checked"
    __table_args__ = (
        Index(
            "ix_claims_checked_duplicate",
            "tenant_id",
            "patient_token",
            "service_code",
            "date_of_service",
        ),
        Index("ix_claims_checked_history", "tenant_id", "checked_at"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    claim_ref: Mapped[str] = mapped_column(String(50))
    patient_token: Mapped[str] = mapped_column(String(64))
    facility_id: Mapped[str] = mapped_column(String(50))
    service_code: Mapped[str] = mapped_column(String(50))
    fund: Mapped[str] = mapped_column(String(10))
    date_of_service: Mapped[date] = mapped_column(Date)
    amount_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    has_preauth: Mapped[bool] = mapped_column(Boolean)
    icd_code: Mapped[str | None] = mapped_column(String(20))
    verdict: Mapped[str] = mapped_column(String(10))
    strength: Mapped[float]
    confidence: Mapped[float]
    revenue_at_risk_kes: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    rulebook_version: Mapped[str] = mapped_column(String(50))
    trace_hash: Mapped[str] = mapped_column(String(71))
    audit_id: Mapped[int] = mapped_column(ForeignKey("audit_log.id"))
    checked_at: Mapped[datetime] = _created_at()
