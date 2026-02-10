"""seed default system roles

Revision ID: a1b2c3d4e5f6
Revises: 03d68951bfd2
Create Date: 2026-02-09 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from uuid_utils import uuid7

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "03d68951bfd2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_table = sa.table(
        "role",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("permissions", sa.JSON),
        sa.column("is_system", sa.Boolean),
        sa.column("scope", sa.String),
    )

    op.bulk_insert(
        role_table,
        [
            {
                "id": str(uuid7()),
                "name": "user",
                "description": "Default system role for registered users",
                "permissions": [],
                "is_system": True,
                "scope": "system",
            },
            {
                "id": str(uuid7()),
                "name": "admin",
                "description": "System administrator with full access",
                "permissions": ["*:*"],
                "is_system": True,
                "scope": "system",
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM role WHERE name IN ('user', 'admin') AND is_system = TRUE")
