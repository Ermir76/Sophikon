"""seed project roles and backfill owner memberships

Revision ID: f1a2b3c4d5e6
Revises: d8e2f4a6c9b1
Create Date: 2026-03-08 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from uuid_utils import uuid7

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "d8e2f4a6c9b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PROJECT_ROLE_SEED = (
    ("owner", "Project owner with full access"),
    ("manager", "Project manager"),
    ("member", "Project member"),
    ("viewer", "Project viewer"),
)


def upgrade() -> None:
    bind = op.get_bind()

    role_table = sa.table(
        "role",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("permissions", sa.JSON),
        sa.column("is_system", sa.Boolean),
        sa.column("scope", sa.String),
    )

    for role_name, description in PROJECT_ROLE_SEED:
        existing = bind.execute(
            sa.text("SELECT id FROM role WHERE name = :name"),
            {"name": role_name},
        ).first()
        if existing is None:
            op.bulk_insert(
                role_table,
                [
                    {
                        "id": str(uuid7()),
                        "name": role_name,
                        "description": description,
                        "permissions": [],
                        "is_system": False,
                        "scope": "project",
                    }
                ],
            )

    owner_role = bind.execute(
        sa.text(
            "SELECT id FROM role WHERE name = 'owner' AND scope = 'project' LIMIT 1"
        )
    ).first()
    if owner_role is None:
        raise RuntimeError("Required project role 'owner' not found after seeding.")

    owner_role_id = owner_role[0]
    missing_owner_rows = bind.execute(
        sa.text(
            """
            SELECT p.id AS project_id, p.owner_id AS user_id
            FROM project p
            LEFT JOIN project_member pm
              ON pm.project_id = p.id
             AND pm.user_id = p.owner_id
            WHERE p.is_deleted = FALSE
              AND pm.id IS NULL
            """
        )
    ).fetchall()

    project_member_table = sa.table(
        "project_member",
        sa.column("id", sa.Uuid),
        sa.column("project_id", sa.Uuid),
        sa.column("user_id", sa.Uuid),
        sa.column("role_id", sa.Uuid),
    )
    if missing_owner_rows:
        op.bulk_insert(
            project_member_table,
            [
                {
                    "id": str(uuid7()),
                    "project_id": row.project_id,
                    "user_id": row.user_id,
                    "role_id": owner_role_id,
                }
                for row in missing_owner_rows
            ],
        )


def downgrade() -> None:
    # No-op downgrade: seeded roles/memberships may be referenced by active data.
    pass
