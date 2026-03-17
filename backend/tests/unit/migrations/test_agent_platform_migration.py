from importlib import util
from pathlib import Path
from types import ModuleType


def _load_migration(filename: str) -> ModuleType:
    root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "alembic").is_dir() and (parent / "app").is_dir()
    )
    path = root / "alembic" / "versions" / filename
    spec = util.spec_from_file_location(filename.replace(".py", ""), path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase1_migration_revision_chain() -> None:
    m = _load_migration("03241aac0f9f_add_agent_platform_columns_and_memory_.py")
    assert m.revision == "03241aac0f9f"
    assert m.down_revision == "a4f2c8d9e7b1"


def test_phase1_migration_has_upgrade_and_downgrade() -> None:
    m = _load_migration("03241aac0f9f_add_agent_platform_columns_and_memory_.py")
    assert callable(m.upgrade)
    assert callable(m.downgrade)


def test_cleanup_migration_revision_chain() -> None:
    m = _load_migration("f7b2e1d4c8a3_drop_orphan_email_verification_index.py")
    assert m.revision == "f7b2e1d4c8a3"
    assert m.down_revision == "03241aac0f9f"


def test_cleanup_migration_has_upgrade_and_downgrade() -> None:
    m = _load_migration("f7b2e1d4c8a3_drop_orphan_email_verification_index.py")
    assert callable(m.upgrade)
    assert callable(m.downgrade)
