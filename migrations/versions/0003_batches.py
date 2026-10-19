"""csv batches and per-claim failing rules

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"


def upgrade() -> None:
    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("filename", sa.String(100), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("total", sa.Integer, nullable=False),
        sa.Column("processed", sa.Integer, nullable=False),
        sa.Column("claims", postgresql.JSONB, nullable=False),
        sa.Column("errors", postgresql.JSONB, nullable=False),
        sa.Column("summary", postgresql.JSONB),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )
    op.add_column("claims_checked", sa.Column("row_number", sa.Integer))
    op.add_column(
        "claims_checked",
        sa.Column("failing_rules", postgresql.JSONB, nullable=False, server_default="[]"),
    )
    op.alter_column("claims_checked", "failing_rules", server_default=None)


def downgrade() -> None:
    op.drop_column("claims_checked", "failing_rules")
    op.drop_column("claims_checked", "row_number")
    op.drop_table("batches")
