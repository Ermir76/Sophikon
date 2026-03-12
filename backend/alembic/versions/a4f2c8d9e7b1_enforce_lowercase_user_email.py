"""enforce lowercase user email

Revision ID: a4f2c8d9e7b1
Revises: e3c9d1a7b2f4
Create Date: 2026-03-12 23:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4f2c8d9e7b1"
down_revision: str | Sequence[str] | None = "e3c9d1a7b2f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _find_case_insensitive_duplicates(
    bind: sa.Connection,
) -> list[tuple[str, list[str]]]:
    rows = bind.execute(
        sa.text(
            """
            SELECT
                lower(email) AS canonical_email,
                array_agg(email ORDER BY email) AS variants
            FROM "user"
            GROUP BY lower(email)
            HAVING count(*) > 1
            """
        )
    ).all()
    return [(str(row.canonical_email), list(row.variants)) for row in rows]


def upgrade() -> None:
    bind = op.get_bind()

    duplicates = _find_case_insensitive_duplicates(bind)
    if duplicates:
        details = "; ".join(
            f"{canonical}: {variants}" for canonical, variants in duplicates
        )
        raise RuntimeError(
            "Cannot enforce lowercase email uniqueness. Resolve duplicate emails first: "
            f"{details}"
        )

    op.execute(
        sa.text('UPDATE "user" SET email = lower(email) WHERE email <> lower(email)')
    )
    op.create_check_constraint(
        "ck_user_email_lowercase",
        "user",
        "email = lower(email)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_email_lowercase", "user", type_="check")
