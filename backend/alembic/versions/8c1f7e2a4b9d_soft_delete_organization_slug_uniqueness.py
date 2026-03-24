"""soft_delete_organization_slug_uniqueness

Revision ID: 8c1f7e2a4b9d
Revises: 39fc0da6c5a7
Create Date: 2026-03-24 11:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c1f7e2a4b9d"
down_revision: str | Sequence[str] | None = "39fc0da6c5a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f("ix_organization_slug"), table_name="organization")
    op.drop_index(
        "idx_organization_slug",
        table_name="organization",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "uq_organization_slug_active",
        "organization",
        ["slug"],
        unique=True,
        postgresql_where=sa.text("NOT is_deleted"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "uq_organization_slug_active",
        table_name="organization",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_organization_slug",
        "organization",
        ["slug"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(op.f("ix_organization_slug"), "organization", ["slug"], unique=True)
