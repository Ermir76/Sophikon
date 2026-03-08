"""add comment entity_type check constraint

Revision ID: 9b8c7d6e5f4a
Revises: f1a2b3c4d5e6
Create Date: 2026-03-08 22:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b8c7d6e5f4a"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ALLOWED_COMMENT_ENTITY_TYPES = (
    "project",
    "task",
    "resource",
    "assignment",
    "dependency",
    "project_member",
)


def _fetch_invalid_comment_entity_types(bind: sa.Connection) -> list[str]:
    allowed_csv = ", ".join(f"'{value}'" for value in ALLOWED_COMMENT_ENTITY_TYPES)
    result = bind.execute(
        sa.text(
            f"""
            SELECT DISTINCT entity_type
            FROM comment
            WHERE entity_type IS NOT NULL
              AND entity_type NOT IN ({allowed_csv})
            ORDER BY entity_type
            """
        )
    )
    return [str(row[0]) for row in result.fetchall()]


def _validate_existing_comment_entity_types(bind: sa.Connection) -> None:
    invalid_values = _fetch_invalid_comment_entity_types(bind)
    if invalid_values:
        invalid_csv = ", ".join(invalid_values)
        raise RuntimeError(
            "Cannot apply check_comment_entity_type because invalid "
            f"comment.entity_type values exist: {invalid_csv}. "
            "Fix these rows before running this migration."
        )


def upgrade() -> None:
    bind = op.get_bind()
    _validate_existing_comment_entity_types(bind)
    op.create_check_constraint(
        "check_comment_entity_type",
        "comment",
        "entity_type IN ('project', 'task', 'resource', 'assignment', 'dependency', 'project_member')",
    )


def downgrade() -> None:
    op.drop_constraint("check_comment_entity_type", "comment", type_="check")
