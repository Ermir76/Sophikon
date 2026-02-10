"""
Dependency business logic.

Handles listing, creating, updating, and deleting task dependencies.
Note: Dependencies use hard delete.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency import Dependency
from app.models.project import Project
from app.models.task import Task
from app.schema.dependency import DependencyCreate, DependencyUpdate


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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label} task not found in this project",
            )


async def create_dependency(
    db: AsyncSession,
    project: Project,
    data: DependencyCreate,
) -> Dependency:
    """Create a new dependency between tasks."""
    # Validate both tasks exist in the project
    await _validate_tasks_in_project(
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
        await db.commit()
        await db.refresh(dependency)
        return dependency
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This dependency already exists",
        )


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
) -> Dependency:
    """Update a dependency with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dependency, field, value)

    await db.commit()
    await db.refresh(dependency)
    return dependency


async def delete_dependency(
    db: AsyncSession,
    dependency: Dependency,
) -> None:
    """Hard delete a dependency."""
    await db.delete(dependency)
    await db.commit()
