"""Add color column to project and task

Revision ID: d8e2f4a6c9b1
Revises: c7a1e2f3b4d5
Create Date: 2026-03-01 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d8e2f4a6c9b1"
down_revision = "c7a1e2f3b4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("project", sa.Column("color", sa.String(80), nullable=True))
    op.add_column("task", sa.Column("color", sa.String(80), nullable=True))


def downgrade() -> None:
    op.drop_column("task", "color")
    op.drop_column("project", "color")
