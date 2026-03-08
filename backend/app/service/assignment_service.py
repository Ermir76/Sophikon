"""
Assignment business logic.

Handles listing, creating, updating, and deleting resource assignments.
Note: Assignments use hard delete.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidOperationError,
    ResourceConflictError,
)
from app.models.assignment import Assignment
from app.models.enums import AuditAction
from app.models.resource import Resource
from app.models.task import Task
from app.schema.assignment import AssignmentCreate, AssignmentUpdate
from app.service import activity_log_service, realtime_service
from app.service.activity_log_service import ActivityContext


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
) -> Resource:
    """Validate resource exists and belongs to the project."""
    result = await db.execute(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.project_id == project_id,
        )
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise InvalidOperationError("Resource not found in this project")
    return resource


async def _get_assignment_label(
    db: AsyncSession,
    assignment: Assignment,
) -> str:
    resource_result = await db.execute(
        select(Resource.name).where(Resource.id == assignment.resource_id)
    )
    resource_name = resource_result.scalar_one_or_none() or str(assignment.resource_id)
    task_result = await db.execute(
        select(Task.name).where(Task.id == assignment.task_id)
    )
    task_name = task_result.scalar_one_or_none() or str(assignment.task_id)
    return f"{resource_name} -> {task_name}"


async def create_assignment(
    db: AsyncSession,
    task: Task,
    data: AssignmentCreate,
    activity_context: ActivityContext | None = None,
) -> Assignment:
    """Create a new assignment for a task."""
    # Validate resource is in the same project
    resource = await _validate_resource_in_project(
        db, data.resource_id, task.project_id
    )

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
        await db.flush()
        await activity_log_service.log_activity(
            db,
            project_id=task.project_id,
            action=AuditAction.CREATED,
            entity_type="assignment",
            entity_id=assignment.id,
            entity_name=f"{resource.name} -> {task.name}",
            context=activity_context,
        )
        realtime_service.queue_entity_event(
            db,
            project_id=task.project_id,
            entity_type="assignment",
            action=AuditAction.CREATED,
            entity_id=assignment.id,
            entity_name=f"{resource.name} -> {task.name}",
            context=activity_context,
            metadata={
                "task_id": assignment.task_id,
                "resource_id": assignment.resource_id,
            },
        )
        await realtime_service.commit_and_publish(db)
        await db.refresh(assignment)
        return assignment
    except IntegrityError:
        await realtime_service.rollback_and_clear(db)
        raise ResourceConflictError("This resource is already assigned to this task")


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
    activity_context: ActivityContext | None = None,
) -> None:
    """Hard delete an assignment."""
    assignment_label = await _get_assignment_label(db, assignment)
    task_result = await db.execute(
        select(Task.project_id).where(Task.id == assignment.task_id)
    )
    project_id = task_result.scalar_one_or_none()
    await activity_log_service.log_activity(
        db,
        project_id=project_id,
        action=AuditAction.DELETED,
        entity_type="assignment",
        entity_id=assignment.id,
        entity_name=assignment_label,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=project_id,
        entity_type="assignment",
        action=AuditAction.DELETED,
        entity_id=assignment.id,
        entity_name=assignment_label,
        context=activity_context,
        metadata={
            "task_id": assignment.task_id,
            "resource_id": assignment.resource_id,
        },
    )
    await db.delete(assignment)
    await realtime_service.commit_and_publish(db)
