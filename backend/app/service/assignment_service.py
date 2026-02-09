"""
Assignment business logic.

Handles listing, creating, updating, and deleting resource assignments.
Note: Assignments use hard delete.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.resource import Resource
from app.models.task import Task
from app.schema.assignment import AssignmentCreate, AssignmentUpdate


async def list_assignments_by_task(
    db: AsyncSession,
    task: Task,
) -> list[Assignment]:
    """List all assignments for a task."""
    result = await db.execute(
        select(Assignment)
        .where(Assignment.task_id == task.id)
        .order_by(Assignment.created_at.asc())
    )
    return list(result.scalars().all())


async def _validate_resource_in_project(
    db: AsyncSession,
    resource_id: UUID,
    project_id: UUID,
) -> None:
    """Validate resource exists and belongs to the project."""
    result = await db.execute(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.project_id == project_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource not found in this project",
        )


async def create_assignment(
    db: AsyncSession,
    task: Task,
    data: AssignmentCreate,
) -> Assignment:
    """Create a new assignment for a task."""
    # Validate resource is in the same project
    await _validate_resource_in_project(db, data.resource_id, task.project_id)

    assignment = Assignment(
        task_id=task.id,
        resource_id=data.resource_id,
        units=data.units,
        start_date=data.start_date,
        finish_date=data.finish_date,
        work=data.work,
        remaining_work=data.work,
        work_contour=data.work_contour,
        rate_table=data.rate_table,
    )

    try:
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This resource is already assigned to this task",
        )


async def get_assignment_by_id(
    db: AsyncSession,
    assignment_id: UUID,
) -> Assignment | None:
    """Get an assignment by ID."""
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    return result.scalar_one_or_none()


async def update_assignment(
    db: AsyncSession,
    assignment: Assignment,
    data: AssignmentUpdate,
) -> Assignment:
    """Update an assignment with partial data."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)

    await db.commit()
    await db.refresh(assignment)
    return assignment


async def delete_assignment(
    db: AsyncSession,
    assignment: Assignment,
) -> None:
    """Hard delete an assignment."""
    await db.delete(assignment)
    await db.commit()
