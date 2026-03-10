from importlib import util
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import pytest


def _load_migration_module() -> ModuleType:
    root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "alembic").is_dir() and (parent / "app").is_dir()
    )
    path = (
        root
        / "alembic"
        / "versions"
        / "e3c9d1a7b2f4_enforce_comment_thread_integrity.py"
    )
    spec = util.spec_from_file_location("comment_thread_integrity_migration", path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validation_allows_valid_hierarchy() -> None:
    migration = _load_migration_module()
    entity_id = uuid4()
    root_id = uuid4()
    child_id = uuid4()
    rows = [
        migration._CommentRow(
            id=root_id,
            parent_comment_id=None,
            entity_type="task",
            entity_id=entity_id,
            is_deleted=False,
        ),
        migration._CommentRow(
            id=child_id,
            parent_comment_id=root_id,
            entity_type="task",
            entity_id=entity_id,
            is_deleted=False,
        ),
    ]

    migration._validate_existing_comment_hierarchy_rows(rows)


def test_validation_rejects_cycle() -> None:
    migration = _load_migration_module()
    entity_id = uuid4()
    a_id = uuid4()
    b_id = uuid4()
    rows = [
        migration._CommentRow(
            id=a_id,
            parent_comment_id=b_id,
            entity_type="task",
            entity_id=entity_id,
            is_deleted=False,
        ),
        migration._CommentRow(
            id=b_id,
            parent_comment_id=a_id,
            entity_type="task",
            entity_id=entity_id,
            is_deleted=False,
        ),
    ]

    with pytest.raises(RuntimeError, match="cycle detected"):
        migration._validate_existing_comment_hierarchy_rows(rows)


def test_validation_rejects_depth_over_limit() -> None:
    migration = _load_migration_module()
    entity_id = uuid4()

    previous_id = None
    rows = []
    for _ in range(migration.COMMENT_MAX_THREAD_DEPTH + 1):
        comment_id = uuid4()
        rows.append(
            migration._CommentRow(
                id=comment_id,
                parent_comment_id=previous_id,
                entity_type="task",
                entity_id=entity_id,
                is_deleted=False,
            )
        )
        previous_id = comment_id

    with pytest.raises(RuntimeError, match="depth exceeds"):
        migration._validate_existing_comment_hierarchy_rows(rows)


def test_validation_rejects_parent_entity_mismatch() -> None:
    migration = _load_migration_module()
    root_id = uuid4()
    rows = [
        migration._CommentRow(
            id=root_id,
            parent_comment_id=None,
            entity_type="task",
            entity_id=uuid4(),
            is_deleted=False,
        ),
        migration._CommentRow(
            id=uuid4(),
            parent_comment_id=root_id,
            entity_type="project",
            entity_id=uuid4(),
            is_deleted=False,
        ),
    ]

    with pytest.raises(RuntimeError, match="entity mismatch"):
        migration._validate_existing_comment_hierarchy_rows(rows)
