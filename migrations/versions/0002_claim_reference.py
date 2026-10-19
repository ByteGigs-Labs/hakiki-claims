"""claim reference for duplicate detection

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.add_column(
        "claims_checked", sa.Column("claim_ref", sa.String(50), nullable=False, server_default="")
    )
    op.alter_column("claims_checked", "claim_ref", server_default=None)


def downgrade() -> None:
    op.drop_column("claims_checked", "claim_ref")
