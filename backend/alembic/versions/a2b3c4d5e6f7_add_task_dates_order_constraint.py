"""add task dates order constraint

Revision ID: a2b3c4d5e6f7
Revises: 7e9a4c2b1d8f
Create Date: 2026-04-01 10:30:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: str | Sequence[str] | None = "7e9a4c2b1d8f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Fix any existing rows where finish_date < start_date
    op.execute(
        sa.text(
            """
            UPDATE task
            SET finish_date = start_date
            WHERE finish_date < start_date
            """
        )
    )

    op.create_check_constraint(
        "check_task_dates_order",
        "task",
        "finish_date >= start_date",
    )


def downgrade() -> None:
    op.drop_constraint("check_task_dates_order", "task", type_="check")
