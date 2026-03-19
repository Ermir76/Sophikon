"""add task status column

Revision ID: b3c4d5e6f7a8
Revises: f7b2e1d4c8a3
Create Date: 2026-03-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: str | None = "f7b2e1d4c8a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "task",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'BACKLOG'"),
        ),
    )
    op.create_index("idx_task_status", "task", ["status"])


def downgrade() -> None:
    op.drop_index("idx_task_status", table_name="task")
    op.drop_column("task", "status")
