"""
Task CRUD endpoints.

GET    /projects/{project_id}/tasks              - List project tasks
POST   /projects/{project_id}/tasks              - Create a new task
GET    /projects/{project_id}/tasks/{task_id}    - Get task details
PATCH  /projects/{project_id}/tasks/{task_id}    - Update task
DELETE /projects/{project_id}/tasks/{task_id}    - Soft delete task
POST   /projects/{project_id}/tasks/{task_id}/indent  - Indent task
POST   /projects/{project_id}/tasks/{task_id}/outdent - Outdent task
POST   /projects/{project_id}/tasks/{task_id}/reorder - Reorder task
POST   /projects/{project_id}/tasks/bulk              - Bulk create tasks
PATCH  /projects/{project_id}/tasks/bulk              - Bulk update tasks
DELETE /projects/{project_id}/tasks/bulk              - Bulk delete tasks
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.api.deps.project import (
    ProjectAccess,
    check_role,
    get_project_or_404,
)
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schema.common import PaginatedResponse
from app.schema.task import (
    BulkOperationResponse,
    TaskBulkCreate,
    TaskBulkCreateResponse,
    TaskBulkDelete,
    TaskBulkUpdate,
    TaskCreate,
    TaskReorder,
    TaskResponse,
    TaskUpdate,
)
from app.service import (
    activity_log_service,
    realtime_service,
    task_bulk_service,
    task_hierarchy_service,
    task_service,
)

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=1000)] = 50,
    include_deleted: Annotated[bool, Query()] = False,
):
    """List all tasks in the project."""
    if include_deleted:
        check_role(access, "owner", "manager")

    tasks, total = await task_service.list_tasks(
        db,
        access.project,
        page=page,
        per_page=per_page,
        include_deleted=include_deleted,
    )
    return PaginatedResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """Create a new task in the project."""
    check_role(access, "owner", "manager", "member")
    task = await task_service.create_task(
        db,
        access.project,
        body.model_dump(mode="python"),
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    return TaskResponse.model_validate(task)


@router.post("/bulk", response_model=TaskBulkCreateResponse)
async def bulk_create_tasks(
    body: TaskBulkCreate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """
    Bulk create tasks.
    """
    check_role(access, "owner", "manager", "member")
    tasks, errors = await task_bulk_service.bulk_create_tasks(
        db,
        access.project,
        [task.model_dump(mode="python") for task in body.tasks],
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    return {
        "tasks": [TaskResponse.model_validate(t) for t in tasks],
        "errors": errors,
    }


@router.patch("/bulk", response_model=BulkOperationResponse)
async def bulk_update_tasks(
    body: TaskBulkUpdate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """
    Bulk update tasks.
    """
    check_role(access, "owner", "manager", "member")
    succeeded, failed, errors = await task_bulk_service.bulk_update_tasks(
        db,
        access.project,
        [
            {
                "id": task.id,
                "data": task.data.model_dump(mode="python", exclude_unset=True),
            }
            for task in body.tasks
        ],
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    return {"succeeded": succeeded, "failed": failed, "errors": errors}


@router.delete("/bulk", response_model=BulkOperationResponse)
async def bulk_delete_tasks(
    body: TaskBulkDelete,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """
    Bulk soft-delete tasks.
    """
    check_role(access, "owner", "manager")
    succeeded, failed, errors = await task_bulk_service.bulk_delete_tasks(
        db,
        access.project,
        body.task_ids,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    return {"succeeded": succeeded, "failed": failed, "errors": errors}


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get task details."""
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise NotFoundError("Task not found")
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    body: TaskUpdate,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """Update a task."""
    check_role(access, "owner", "manager", "member")
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise NotFoundError("Task not found")

    task = await task_service.update_task(
        db,
        task,
        body.model_dump(mode="python", exclude_unset=True),
        access.project,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """Soft delete a task."""
    check_role(access, "owner", "manager")
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise NotFoundError("Task not found")

    await task_service.soft_delete_task(
        db,
        task,
        access.project,
        activity_context=activity_log_service.activity_context_from_request(
            user,
            request,
        ),
    )
    # Unlike soft_delete_project/organization which commit internally,
    # soft_delete_task is recursive (deleting child tasks). We flush
    # internally and commit once here to avoid partial commits.
    await realtime_service.commit_and_publish(db)


@router.post("/{task_id}/indent", response_model=TaskResponse)
async def indent_task(
    task_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Indent a task in the project hierarchy."""
    check_role(access, "owner", "manager", "member")
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise NotFoundError("Task not found")

    task = await task_hierarchy_service.indent_task(db, access.project, task)
    return TaskResponse.model_validate(task)


@router.post("/{task_id}/outdent", response_model=TaskResponse)
async def outdent_task(
    task_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Outdent a task in the project hierarchy."""
    check_role(access, "owner", "manager", "member")
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise NotFoundError("Task not found")

    task = await task_hierarchy_service.outdent_task(db, access.project, task)
    return TaskResponse.model_validate(task)


@router.post("/{task_id}/reorder", response_model=TaskResponse)
async def reorder_task(
    task_id: UUID,
    body: TaskReorder,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Reorder a task via drag-and-drop.
    """
    check_role(access, "owner", "manager", "member")
    task = await task_service.get_task_by_id(db, task_id, access.project.id)
    if not task:
        raise NotFoundError("Task not found")

    task = await task_hierarchy_service.reorder_task(
        db,
        access.project,
        task,
        after_task_id=body.after_task_id,
        before_task_id=body.before_task_id,
        new_parent_id=body.new_parent_id,
    )
    return TaskResponse.model_validate(task)
