"""status_thresholds_and_task_status_backfill

Revision ID: 6f2c1d9a8b4e
Revises: 8c1f7e2a4b9d
Create Date: 2026-03-27 09:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6f2c1d9a8b4e"
down_revision: str | Sequence[str] | None = "8c1f7e2a4b9d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE project
        SET settings = jsonb_set(
            COALESCE(settings, '{}'::jsonb),
            '{status_thresholds}',
            COALESCE(
                settings->'status_thresholds',
                '{"IN_PROGRESS": 1, "IN_REVIEW": 80, "DONE": 100}'::jsonb
            ),
            true
        )
        """
    )
    op.execute(
        """
        UPDATE task
        SET status = CASE
            WHEN percent_complete >= 100 THEN 'DONE'
            WHEN percent_complete >= 80 THEN 'IN_REVIEW'
            WHEN percent_complete > 0 THEN 'IN_PROGRESS'
            WHEN percent_complete = 0 AND status = 'BACKLOG' THEN 'BACKLOG'
            ELSE 'TODO'
        END
        WHERE is_deleted = FALSE
        """
    )


def downgrade() -> None:
    pass
