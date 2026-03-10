"""
Assignment business logic.

Handles listing, creating, updating, and deleting resource assignments.
Note: Assignments use hard delete.
"""

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidOperationError,
    ResourceConflictError,
)
from app.models.assignment import Assignment
from app.models.enums import AuditAction, NotificationType
from app.models.resource import Resource
from app.models.task import Task
from app.repository import assignment_repo
from app.service import activity_log_service, notification_service, realtime_service
from app.service.activity_log_service import ActivityContext
from app.service.contracts.assignment import AssignmentCreateInput, AssignmentPatchInput


async def list_assignments_by_task(
    db: AsyncSession,
    task: Task,
) -> list[Assignment]:
    """List all assignments for a task."""
    return await assignment_repo.list_for_task(db, task_id=task.id)


async def _validate_resource_in_project(
    db: AsyncSession,
    resource_id: UUID,
    project_id: UUID,
) -> Resource:
    """Validate resource exists and belongs to the project."""
    resource = await assignment_repo.get_resource_in_project(
        db,
        resource_id=resource_id,
        project_id=project_id,
    )
    if not resource:
        raise InvalidOperationError("Resource not found in this project")
    return resource


async def _get_assignment_label(
    db: AsyncSession,
    assignment: Assignment,
) -> str:
    resource_name, task_name = await assignment_repo.get_assignment_label_parts(
        db,
        assignment=assignment,
    )
    resource_name = resource_name or str(assignment.resource_id)
    task_name = task_name or str(assignment.task_id)
    return f"{resource_name} -> {task_name}"


async def create_assignment(
    db: AsyncSession,
    task: Task,
    payload: AssignmentCreateInput,
    activity_context: ActivityContext | None = None,
) -> Assignment:
    """Create a new assignment for a task."""
    # Validate resource is in the same project
    resource = await _validate_resource_in_project(
        db, payload["resource_id"], task.project_id
    )

    try:
        assignment = await assignment_repo.create(
            db,
            task_id=task.id,
            payload=payload,
        )
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
        actor_id = activity_context.user_id if activity_context else None
        if resource.user_id is not None and resource.user_id != actor_id:
            actor_name = activity_context.full_name if activity_context else None
            await notification_service.create_notification(
                db,
                user_id=resource.user_id,
                type=NotificationType.TASK_ASSIGNED,
                title="You were assigned to a task",
                message=(
                    f"{actor_name or 'A teammate'} assigned you to '{task.name}'."
                ),
                entity_type="task",
                entity_id=task.id,
                actor_id=actor_id,
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
    return await assignment_repo.get_by_id(db, assignment_id=assignment_id)


async def update_assignment(
    db: AsyncSession,
    assignment: Assignment,
    patch: AssignmentPatchInput,
    activity_context: ActivityContext | None = None,
) -> Assignment:
    """Update an assignment with partial data."""
    before = {field: getattr(assignment, field) for field in patch}
    for field, value in patch.items():
        setattr(assignment, field, value)

    project_id = await assignment_repo.get_task_project_id(
        db,
        task_id=assignment.task_id,
    )
    if project_id is None:
        raise InvalidOperationError(
            "Cannot update assignment because parent task project was not found"
        )

    changes = activity_log_service.build_change_set(
        before,
        {field: getattr(assignment, field) for field in patch},
    )
    if changes is not None:
        assignment_label = await _get_assignment_label(db, assignment)
        await activity_log_service.log_activity(
            db,
            project_id=project_id,
            action=AuditAction.UPDATED,
            entity_type="assignment",
            entity_id=assignment.id,
            entity_name=assignment_label,
            changes=changes,
            context=activity_context,
        )
        realtime_service.queue_entity_event(
            db,
            project_id=project_id,
            entity_type="assignment",
            action=AuditAction.UPDATED,
            entity_id=assignment.id,
            entity_name=assignment_label,
            context=activity_context,
            metadata={
                "task_id": assignment.task_id,
                "resource_id": assignment.resource_id,
                "changes": changes,
            },
        )

    await realtime_service.commit_and_publish(db)
    await db.refresh(assignment)
    return assignment


async def delete_assignment(
    db: AsyncSession,
    assignment: Assignment,
    activity_context: ActivityContext | None = None,
) -> None:
    """Hard delete an assignment."""
    assignment_label = await _get_assignment_label(db, assignment)
    project_id = await assignment_repo.get_task_project_id(
        db,
        task_id=assignment.task_id,
    )
    if project_id is None:
        raise InvalidOperationError(
            "Cannot delete assignment because parent task project was not found"
        )
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
