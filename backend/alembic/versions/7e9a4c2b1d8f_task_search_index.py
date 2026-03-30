"""task_search_index

Revision ID: 7e9a4c2b1d8f
Revises: 6f2c1d9a8b4e
Create Date: 2026-03-30 11:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e9a4c2b1d8f"
down_revision: str | Sequence[str] | None = "6f2c1d9a8b4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_task_search_vector
        ON task
        USING gin (to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(notes, '')))
        WHERE NOT is_deleted
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_task_search_vector")
