"""per-sibling order_index and sort_order column

Revision ID: c7a1e2f3b4d5
Revises: b6f3a6c8b4aa
Create Date: 2026-02-25 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7a1e2f3b4d5"
down_revision: str | Sequence[str] | None = "b6f3a6c8b4aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop global order index, add per-sibling index and sort_order column."""
    op.drop_index(
        "idx_task_project_order",
        table_name="task",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_task_sibling_order",
        "task",
        ["project_id", "parent_task_id", "order_index"],
        unique=True,
        postgresql_where=sa.text("NOT is_deleted AND parent_task_id IS NOT NULL"),
    )
    op.create_index(
        "idx_task_root_order",
        "task",
        ["project_id", "order_index"],
        unique=True,
        postgresql_where=sa.text("NOT is_deleted AND parent_task_id IS NULL"),
    )
    op.add_column(
        "task",
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    """Restore global order index, drop per-sibling index and sort_order."""
    op.drop_column("task", "sort_order")
    op.drop_index(
        "idx_task_root_order",
        table_name="task",
        postgresql_where=sa.text("NOT is_deleted AND parent_task_id IS NULL"),
    )
    op.drop_index(
        "idx_task_sibling_order",
        table_name="task",
        postgresql_where=sa.text("NOT is_deleted AND parent_task_id IS NOT NULL"),
    )
    op.create_index(
        "idx_task_project_order",
        "task",
        ["project_id", "order_index"],
        unique=True,
        postgresql_where=sa.text("NOT is_deleted"),
    )
