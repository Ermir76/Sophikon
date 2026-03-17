"""drop orphan ix_email_verification_user_id index

The original email_verification migration (b6f3a6c8b4aa) accidentally created
two indexes on user_id: the intentional named index (idx_email_verification_user)
and an autogenerate-style index (ix_email_verification_user_id). The model only
declares the named one, so autogenerate kept detecting the orphan and polluting
every subsequent migration. This migration removes the orphan once.

Revision ID: f7b2e1d4c8a3
Revises: 03241aac0f9f
Create Date: 2026-03-17

"""

from collections.abc import Sequence

from alembic import op

revision: str = "f7b2e1d4c8a3"
down_revision: str | Sequence[str] | None = "03241aac0f9f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_email_verification_user_id", table_name="email_verification")


def downgrade() -> None:
    op.create_index(
        "ix_email_verification_user_id", "email_verification", ["user_id"], unique=False
    )
