"""
Dependency business logic.

Handles listing, creating, updating, and deleting task dependencies.
Note: Dependencies use hard delete.
"""

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidOperationError,
    ResourceConflictError,
)
from app.models.dependency import Dependency
from app.models.enums import AuditAction
from app.models.project import Project
from app.repository import dependency_repo
from app.service import activity_log_service, realtime_service, scheduling_service
from app.service.activity_log_service import ActivityContext
from app.service.contracts.dependency import DependencyCreateInput, DependencyPatchInput


async def _get_task_name(db: AsyncSession, task_id: UUID) -> str:
    return await dependency_repo.get_task_name(db, task_id=task_id) or str(task_id)


async def list_dependencies(
    db: AsyncSession,
    project: Project,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Dependency], int]:
    """List dependencies with pagination."""
    return await dependency_repo.list_for_project(
        db,
        project_id=project.id,
        page=page,
        per_page=per_page,
    )


async def _validate_tasks_in_project(
    db: AsyncSession,
    project_id: UUID,
    predecessor_id: UUID,
    successor_id: UUID,
) -> None:
    """Validate both tasks exist and belong to the project."""
    for task_id, label in [
        (predecessor_id, "Predecessor"),
        (successor_id, "Successor"),
    ]:
        task = await dependency_repo.get_active_task_in_project(
            db,
            task_id=task_id,
            project_id=project_id,
        )
        if task is None:
            raise InvalidOperationError(f"{label} task not found in this project")


async def _check_for_circular_dependency(
    db: AsyncSession,
    project_id: UUID,
    predecessor_id: UUID,
    successor_id: UUID,
) -> None:
    """
    Check if adding an edge from predecessor_id -> successor_id creates a cycle.
    Raises InvalidOperationError if a cycle is detected.
    """
    existing_edges = await dependency_repo.list_edges_for_project(
        db,
        project_id=project_id,
    )

    # Build adjacency list
    graph: dict[UUID, list[UUID]] = {}
    for pred, succ in existing_edges:
        graph.setdefault(pred, []).append(succ)

    # Add the tentative new edge
    graph.setdefault(predecessor_id, []).append(successor_id)

    # DFS from the successor to see if we can reach the predecessor
    visited = set()
    stack = [successor_id]

    while stack:
        node = stack.pop()
        if node == predecessor_id:
            raise InvalidOperationError(
                "Adding this dependency would create a circular reference"
            )

        if node not in visited:
            visited.add(node)
            for neighbor in graph.get(node, []):
                stack.append(neighbor)


async def create_dependency(
    db: AsyncSession,
    project: Project,
    payload: DependencyCreateInput,
    activity_context: ActivityContext | None = None,
) -> Dependency:
    """Create a new dependency between tasks."""
    if payload["predecessor_id"] == payload["successor_id"]:
        raise InvalidOperationError("A task cannot depend on itself")

    # Validate both tasks exist in the project
    await _validate_tasks_in_project(
        db, project.id, payload["predecessor_id"], payload["successor_id"]
    )

    # TODO(concurrency): if dependency write access is delegated to members,
    # serialize create flow per project (for example SELECT ... FOR UPDATE on
    # the project row) before cycle check + insert to avoid race-created cycles.
    await _check_for_circular_dependency(
        db, project.id, payload["predecessor_id"], payload["successor_id"]
    )

    try:
        dependency = await dependency_repo.create(
            db,
            project_id=project.id,
            payload=payload,
        )
        await activity_log_service.log_activity(
            db,
            project_id=project.id,
            action=AuditAction.CREATED,
            entity_type="dependency",
            entity_id=dependency.id,
            entity_name=(
                f"{await _get_task_name(db, dependency.predecessor_id)}"
                f" -> {await _get_task_name(db, dependency.successor_id)}"
            ),
            context=activity_context,
        )
        realtime_service.queue_entity_event(
            db,
            project_id=project.id,
            entity_type="dependency",
            action=AuditAction.CREATED,
            entity_id=dependency.id,
            entity_name=(
                f"{await _get_task_name(db, dependency.predecessor_id)}"
                f" -> {await _get_task_name(db, dependency.successor_id)}"
            ),
            context=activity_context,
            metadata={
                "predecessor_id": dependency.predecessor_id,
                "successor_id": dependency.successor_id,
            },
        )

        # Auto-recalculate schedule after dependency creation
        if project.settings.get("auto_calculate", True):
            await scheduling_service.calculate_schedule(db, project)

        await realtime_service.commit_and_publish(db)
        await db.refresh(dependency)
        return dependency
    except IntegrityError:
        await realtime_service.rollback_and_clear(db)
        raise ResourceConflictError("This dependency already exists")


async def get_dependency_by_id(
    db: AsyncSession,
    dependency_id: UUID,
    project_id: UUID,
) -> Dependency | None:
    """Get a dependency by ID within a project."""
    return await dependency_repo.get_by_id(
        db,
        dependency_id=dependency_id,
        project_id=project_id,
    )


async def update_dependency(
    db: AsyncSession,
    dependency: Dependency,
    patch: DependencyPatchInput,
    project: Project | None = None,
) -> Dependency:
    """Update a dependency with partial data."""
    for field, value in patch.items():
        setattr(dependency, field, value)

    await db.flush()

    # Auto-recalculate schedule after dependency update
    if project and project.settings.get("auto_calculate", True):
        await scheduling_service.calculate_schedule(db, project)

    await db.commit()
    await db.refresh(dependency)
    return dependency


async def delete_dependency(
    db: AsyncSession,
    dependency: Dependency,
    project: Project | None = None,
    activity_context: ActivityContext | None = None,
) -> None:
    """Hard delete a dependency."""
    project_id = project.id if project is not None else dependency.project_id
    await activity_log_service.log_activity(
        db,
        project_id=project_id,
        action=AuditAction.DELETED,
        entity_type="dependency",
        entity_id=dependency.id,
        entity_name=(
            f"{await _get_task_name(db, dependency.predecessor_id)}"
            f" -> {await _get_task_name(db, dependency.successor_id)}"
        ),
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=project_id,
        entity_type="dependency",
        action=AuditAction.DELETED,
        entity_id=dependency.id,
        entity_name=(
            f"{await _get_task_name(db, dependency.predecessor_id)}"
            f" -> {await _get_task_name(db, dependency.successor_id)}"
        ),
        context=activity_context,
        metadata={
            "predecessor_id": dependency.predecessor_id,
            "successor_id": dependency.successor_id,
        },
    )
    await db.delete(dependency)
    await db.flush()

    # Auto-recalculate schedule after dependency deletion
    if project and project.settings.get("auto_calculate", True):
        await scheduling_service.calculate_schedule(db, project)

    await realtime_service.commit_and_publish(db)
