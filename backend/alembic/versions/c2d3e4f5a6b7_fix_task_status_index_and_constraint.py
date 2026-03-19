"""fix task status: add check constraint and partial index

Revision ID: c2d3e4f5a6b7
Revises: b3c4d5e6f7a8
Create Date: 2026-03-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "check_task_status",
        "task",
        "status IN ('BACKLOG', 'TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE')",
    )
    op.drop_index("idx_task_status", table_name="task")
    op.create_index(
        "idx_task_status",
        "task",
        ["status"],
        postgresql_where=sa.text("NOT is_deleted"),
    )


def downgrade() -> None:
    op.drop_index("idx_task_status", table_name="task")
    op.create_index("idx_task_status", "task", ["status"])
    op.drop_constraint("check_task_status", "task", type_="check")
