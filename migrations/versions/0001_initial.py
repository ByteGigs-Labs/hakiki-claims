"""initial schema

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None

UUID = postgresql.UUID(as_uuid=True)
NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_table(
        "sessions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("claim_ref", sa.String(100), nullable=False),
        sa.Column("rulebook_version", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("trace_hash", sa.String(71), nullable=False),
        sa.Column("prev_hash", sa.String(71), nullable=False),
        sa.Column("entry_hash", sa.String(71), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint("tenant_id", "seq"),
    )
    op.create_table(
        "claims_checked",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("batch_id", UUID, index=True),
        sa.Column("patient_token", sa.String(64), nullable=False),
        sa.Column("facility_id", sa.String(50), nullable=False),
        sa.Column("service_code", sa.String(50), nullable=False),
        sa.Column("fund", sa.String(10), nullable=False),
        sa.Column("date_of_service", sa.Date, nullable=False),
        sa.Column("amount_kes", sa.Numeric(12, 2), nullable=False),
        sa.Column("has_preauth", sa.Boolean, nullable=False),
        sa.Column("icd_code", sa.String(20)),
        sa.Column("verdict", sa.String(10), nullable=False),
        sa.Column("strength", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("revenue_at_risk_kes", sa.Numeric(12, 2), nullable=False),
        sa.Column("rulebook_version", sa.String(50), nullable=False),
        sa.Column("trace_hash", sa.String(71), nullable=False),
        sa.Column("audit_id", sa.BigInteger, sa.ForeignKey("audit_log.id"), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index(
        "ix_claims_checked_duplicate",
        "claims_checked",
        ["tenant_id", "patient_token", "service_code", "date_of_service"],
    )
    op.create_index("ix_claims_checked_history", "claims_checked", ["tenant_id", "checked_at"])
    op.execute(
        """
        CREATE FUNCTION audit_log_immutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_immutable
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION audit_log_immutable()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER audit_log_immutable ON audit_log")
    op.execute("DROP FUNCTION audit_log_immutable()")
    for table in ("claims_checked", "audit_log", "sessions", "users", "tenants"):
        op.drop_table(table)
