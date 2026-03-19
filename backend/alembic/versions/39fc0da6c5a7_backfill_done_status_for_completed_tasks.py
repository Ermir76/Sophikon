"""backfill_done_status_for_completed_tasks

Revision ID: 39fc0da6c5a7
Revises: c2d3e4f5a6b7
Create Date: 2026-03-19 21:39:11.934876

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "39fc0da6c5a7"
down_revision: str | Sequence[str] | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE task SET status = 'DONE' WHERE percent_complete = 100 AND is_deleted = FALSE"
    )


def downgrade() -> None:
    pass
