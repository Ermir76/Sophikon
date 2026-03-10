"""enforce comment thread integrity

Revision ID: e3c9d1a7b2f4
Revises: 9b8c7d6e5f4a
Create Date: 2026-03-09 19:20:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple
from uuid import UUID

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3c9d1a7b2f4"
down_revision: str | Sequence[str] | None = "9b8c7d6e5f4a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COMMENT_MAX_THREAD_DEPTH = 32
COMMENT_THREAD_INTEGRITY_FUNCTION = "enforce_comment_thread_integrity"
COMMENT_THREAD_INTEGRITY_TRIGGER = "trg_comment_thread_integrity"


class _CommentRow(NamedTuple):
    id: UUID
    parent_comment_id: UUID | None
    entity_type: str
    entity_id: UUID
    is_deleted: bool


def _fetch_comment_rows(bind: sa.Connection) -> list[_CommentRow]:
    result = bind.execute(
        sa.text(
            """
            SELECT
                id,
                parent_comment_id,
                entity_type,
                entity_id,
                is_deleted
            FROM comment
            """
        )
    )
    rows: list[_CommentRow] = []
    for row in result.fetchall():
        rows.append(
            _CommentRow(
                id=row[0],
                parent_comment_id=row[1],
                entity_type=str(row[2]),
                entity_id=row[3],
                is_deleted=bool(row[4]),
            )
        )
    return rows


def _validate_existing_comment_hierarchy_rows(rows: list[_CommentRow]) -> None:
    by_id = {row.id: row for row in rows}
    errors: list[str] = []

    for row in rows:
        if row.is_deleted:
            continue

        parent_id = row.parent_comment_id
        if parent_id is None:
            continue

        parent = by_id.get(parent_id)
        if parent is None:
            errors.append(f"{row.id}: parent {parent_id} missing")
            continue

        if parent.is_deleted:
            errors.append(f"{row.id}: parent {parent_id} is deleted")
            continue

        if parent.entity_type != row.entity_type or parent.entity_id != row.entity_id:
            errors.append(f"{row.id}: parent {parent_id} entity mismatch")
            continue

        depth = 1
        current_parent_id = parent_id
        seen_ids = {row.id}
        while current_parent_id is not None:
            if current_parent_id in seen_ids:
                errors.append(f"{row.id}: cycle detected through {current_parent_id}")
                break
            seen_ids.add(current_parent_id)

            current_parent = by_id.get(current_parent_id)
            if current_parent is None or current_parent.is_deleted:
                break

            if (
                current_parent.entity_type != row.entity_type
                or current_parent.entity_id != row.entity_id
            ):
                errors.append(f"{row.id}: ancestor {current_parent_id} entity mismatch")
                break

            if depth >= COMMENT_MAX_THREAD_DEPTH:
                errors.append(
                    f"{row.id}: depth exceeds {COMMENT_MAX_THREAD_DEPTH} levels"
                )
                break

            depth += 1
            current_parent_id = current_parent.parent_comment_id

    if errors:
        sample_errors = "; ".join(errors[:10])
        raise RuntimeError(
            "Cannot apply comment thread integrity migration because invalid "
            f"comment hierarchy rows exist: {sample_errors}. "
            "Fix data before running this migration."
        )


def _validate_existing_comment_hierarchy(bind: sa.Connection) -> None:
    _validate_existing_comment_hierarchy_rows(_fetch_comment_rows(bind))


def upgrade() -> None:
    bind = op.get_bind()
    _validate_existing_comment_hierarchy(bind)

    op.execute(
        sa.text(
            f"""
            CREATE FUNCTION {COMMENT_THREAD_INTEGRITY_FUNCTION}()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            DECLARE
                max_depth CONSTANT integer := {COMMENT_MAX_THREAD_DEPTH};
                current_parent_id uuid;
                next_parent_id uuid;
                parent_entity_type text;
                parent_entity_id uuid;
                parent_is_deleted boolean;
                seen_ids uuid[] := ARRAY[]::uuid[];
                depth integer := 1;
            BEGIN
                IF NEW.parent_comment_id IS NULL THEN
                    RETURN NEW;
                END IF;

                IF NEW.id IS NOT NULL AND NEW.parent_comment_id = NEW.id THEN
                    RAISE EXCEPTION 'Comment cannot be its own parent';
                END IF;

                current_parent_id := NEW.parent_comment_id;

                LOOP
                    EXIT WHEN current_parent_id IS NULL;

                    IF current_parent_id = ANY(seen_ids) THEN
                        RAISE EXCEPTION 'Comment ancestry contains a cycle';
                    END IF;
                    seen_ids := array_append(seen_ids, current_parent_id);

                    SELECT
                        c.parent_comment_id,
                        c.entity_type,
                        c.entity_id,
                        c.is_deleted
                    INTO
                        next_parent_id,
                        parent_entity_type,
                        parent_entity_id,
                        parent_is_deleted
                    FROM comment c
                    WHERE c.id = current_parent_id;

                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'Parent comment not found';
                    END IF;

                    IF parent_is_deleted THEN
                        RAISE EXCEPTION 'Cannot reply to a deleted comment';
                    END IF;

                    IF parent_entity_type <> NEW.entity_type OR parent_entity_id <> NEW.entity_id THEN
                        RAISE EXCEPTION 'Parent comment must reference the same entity';
                    END IF;

                    IF NEW.id IS NOT NULL AND current_parent_id = NEW.id THEN
                        RAISE EXCEPTION 'Comment ancestry cannot reference itself';
                    END IF;

                    IF depth >= max_depth THEN
                        RAISE EXCEPTION 'Comment depth exceeds % levels', max_depth;
                    END IF;

                    depth := depth + 1;
                    current_parent_id := next_parent_id;
                END LOOP;

                RETURN NEW;
            END;
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            CREATE TRIGGER {COMMENT_THREAD_INTEGRITY_TRIGGER}
            BEFORE INSERT OR UPDATE OF parent_comment_id, entity_type, entity_id
            ON comment
            FOR EACH ROW
            EXECUTE FUNCTION {COMMENT_THREAD_INTEGRITY_FUNCTION}();
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            f"DROP TRIGGER IF EXISTS {COMMENT_THREAD_INTEGRITY_TRIGGER} ON comment;"
        )
    )
    op.execute(
        sa.text(f"DROP FUNCTION IF EXISTS {COMMENT_THREAD_INTEGRITY_FUNCTION}();")
    )
