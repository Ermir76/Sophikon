"""
Dependency business logic.

Handles listing, creating, updating, and deleting task dependencies.
Note: Dependencies use hard delete.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidOperationError,
    ResourceConflictError,
)
from app.models.dependency import Dependency
from app.models.enums import AuditAction
from app.models.project import Project
from app.models.task import Task
from app.schema.dependency import DependencyCreate, DependencyUpdate
from app.service import activity_log_service, realtime_service, scheduling_service
from app.service.activity_log_service import ActivityContext


async def _get_task_name(db: AsyncSession, task_id: UUID) -> str:
    result = await db.execute(select(Task.name).where(Task.id == task_id))
    return result.scalar_one_or_none() or str(task_id)


async def list_dependencies(
    db: AsyncSession,
    project: Project,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Dependency], int]:
    """List dependencies with pagination."""
    # Count total
    count_result = await db.execute(
        select(func.count()).where(Dependency.project_id == project.id)
    )
    total = count_result.scalar() or 0

    # Get page of items
    result = await db.execute(
        select(Dependency)
        .where(Dependency.project_id == project.id)
        .order_by(Dependency.created_at.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return list(result.scalars().all()), total


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
        result = await db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.project_id == project_id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        if not result.scalar_one_or_none():
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
    result = await db.execute(
        select(Dependency.predecessor_id, Dependency.successor_id).where(
            Dependency.project_id == project_id
        )
    )
    existing_edges = result.all()

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
    data: DependencyCreate,
    activity_context: ActivityContext | None = None,
) -> Dependency:
    """Create a new dependency between tasks."""
    if data.predecessor_id == data.successor_id:
        raise InvalidOperationError("A task cannot depend on itself")

    # Validate both tasks exist in the project
    await _validate_tasks_in_project(
        db, project.id, data.predecessor_id, data.successor_id
    )

    await _check_for_circular_dependency(
        db, project.id, data.predecessor_id, data.successor_id
    )

    dependency = Dependency(
        project_id=project.id,
        predecessor_id=data.predecessor_id,
        successor_id=data.successor_id,
        type=data.type,
        lag=data.lag,
        lag_format=data.lag_format,
    )

    try:
        db.add(dependency)
        await db.flush()
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
    result = await db.execute(
        select(Dependency).where(
            Dependency.id == dependency_id,
            Dependency.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def update_dependency(
    db: AsyncSession,
    dependency: Dependency,
    data: DependencyUpdate,
    project: Project | None = None,
) -> Dependency:
    """Update a dependency with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
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
