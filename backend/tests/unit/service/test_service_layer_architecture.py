from __future__ import annotations

import ast
from pathlib import Path

MIGRATED_SERVICE_MODULES = (
    "assignment_service.py",
    "calendar_service.py",
    "dependency_service.py",
    "organization_member_service.py",
    "organization_service.py",
    "project_member_service.py",
    "project_service.py",
    "resource_service.py",
    "task_service.py",
)


def _find_schema_imports(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module.startswith("app.schema"):
                imports.append(node.module)
    return imports


def test_migrated_services_do_not_import_api_schemas() -> None:
    service_dir = Path(__file__).resolve().parents[3] / "app" / "service"
    violations: list[str] = []

    for filename in MIGRATED_SERVICE_MODULES:
        schema_imports = _find_schema_imports(service_dir / filename)
        if schema_imports:
            imports = ", ".join(sorted(set(schema_imports)))
            violations.append(f"{filename}: {imports}")

    assert not violations, "Schema coupling found in migrated services:\n" + "\n".join(
        violations
    )
