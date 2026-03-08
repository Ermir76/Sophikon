from importlib import util
from pathlib import Path
from types import ModuleType

import pytest


def _load_migration_module() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "9b8c7d6e5f4a_add_comment_entity_type_check_constraint.py"
    )
    spec = util.spec_from_file_location("comment_entity_type_migration", path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeResult:
    def __init__(self, rows: list[tuple[str]]):
        self._rows = rows

    def fetchall(self) -> list[tuple[str]]:
        return self._rows


class _FakeBind:
    def __init__(self, rows: list[str]):
        self._rows = rows

    def execute(self, *_args, **_kwargs) -> _FakeResult:
        return _FakeResult([(row,) for row in self._rows])


def test_migration_validation_allows_known_values() -> None:
    migration = _load_migration_module()
    migration._validate_existing_comment_entity_types(_FakeBind(rows=[]))


def test_migration_validation_rejects_unknown_values() -> None:
    migration = _load_migration_module()
    with pytest.raises(RuntimeError, match="invalid comment.entity_type values exist"):
        migration._validate_existing_comment_entity_types(
            _FakeBind(rows=["legacy_entity"])
        )
