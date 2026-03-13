"""
Task attachment endpoints.

GET    /projects/{project_id}/tasks/{task_id}/attachments
POST   /projects/{project_id}/tasks/{task_id}/attachments
GET    /projects/{project_id}/tasks/{task_id}/attachments/{attachment_id}/download
DELETE /projects/{project_id}/tasks/{task_id}/attachments/{attachment_id}
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.api.deps.project import ProjectAccess, check_role, get_project_or_404
from app.core.attachment_storage import resolve_attachment_path
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schema.attachment import AttachmentResponse
from app.service import attachment_service, task_service

router = APIRouter(
    prefix="/projects/{project_id}/tasks/{task_id}/attachments",
    tags=["attachments"],
)


def _to_attachment_response(
    *,
    project_id: UUID,
    task_id: UUID,
    attachment,
) -> AttachmentResponse:
    return AttachmentResponse(
        id=attachment.id,
        task_id=task_id,
        uploaded_by_id=attachment.uploaded_by_id,
        file_name=attachment.file_name,
        file_size=attachment.file_size,
        mime_type=attachment.mime_type,
        description=attachment.description,
        created_at=attachment.created_at,
        download_url=(
            f"/api/v1/projects/{project_id}/tasks/{task_id}"
            f"/attachments/{attachment.id}/download"
        ),
    )


async def _get_task_or_404(
    db: AsyncSession,
    *,
    project_id: UUID,
    task_id: UUID,
):
    task = await task_service.get_task_by_id(
        db,
        task_id=task_id,
        project_id=project_id,
    )
    if task is None:
        raise NotFoundError("Task not found")
    return task


@router.get("", response_model=list[AttachmentResponse])
async def list_attachments(
    task_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await _get_task_or_404(
        db,
        project_id=access.project.id,
        task_id=task_id,
    )
    attachments = await attachment_service.list_task_attachments(
        db,
        task_id=task.id,
    )
    return [
        _to_attachment_response(
            project_id=access.project.id,
            task_id=task.id,
            attachment=attachment,
        )
        for attachment in attachments
    ]


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(...),
    description: str | None = Form(default=None),
):
    check_role(access, "owner", "manager", "member")
    task = await _get_task_or_404(
        db,
        project_id=access.project.id,
        task_id=task_id,
    )

    file_bytes = await file.read()
    await file.close()

    attachment = await attachment_service.create_task_attachment(
        db,
        task=task,
        uploaded_by_id=user.id,
        file_name=file.filename or "attachment",
        mime_type=file.content_type or "",
        file_bytes=file_bytes,
        description=description,
    )
    return _to_attachment_response(
        project_id=access.project.id,
        task_id=task.id,
        attachment=attachment,
    )


@router.get("/{attachment_id}/download")
async def download_attachment(
    task_id: UUID,
    attachment_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await _get_task_or_404(
        db,
        project_id=access.project.id,
        task_id=task_id,
    )
    attachment = await attachment_service.get_task_attachment_by_id(
        db,
        attachment_id=attachment_id,
        task_id=task.id,
    )
    if attachment is None:
        raise NotFoundError("Attachment not found")

    absolute_path = resolve_attachment_path(attachment.storage_path)
    if absolute_path is None or not absolute_path.exists():
        raise NotFoundError("Attachment file not found")

    return FileResponse(
        path=str(absolute_path),
        media_type=attachment.mime_type,
        filename=attachment.file_name,
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    task_id: UUID,
    attachment_id: UUID,
    access: Annotated[ProjectAccess, Depends(get_project_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    check_role(access, "owner", "manager", "member")
    task = await _get_task_or_404(
        db,
        project_id=access.project.id,
        task_id=task_id,
    )
    attachment = await attachment_service.get_task_attachment_by_id(
        db,
        attachment_id=attachment_id,
        task_id=task.id,
    )
    if attachment is None:
        raise NotFoundError("Attachment not found")

    await attachment_service.delete_task_attachment(db, attachment=attachment)
