"""
Comment endpoints.

GET    /comments/entity/{entity_type}/{entity_id} - List comments for entity
POST   /comments                                  - Create comment
PATCH  /comments/{comment_id}                     - Update comment
DELETE /comments/{comment_id}                     - Soft delete comment
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.api.deps.project import (
    check_role_name,
    get_project_membership_for_user,
)
from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.user import User
from app.schema.comment import (
    CommentCreate,
    CommentEntityType,
    CommentItem,
    CommentListResponse,
    CommentUpdate,
)
from app.service import activity_log_service, comment_service

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/entity/{entity_type}/{entity_id}", response_model=CommentListResponse)
async def list_comments(
    entity_type: CommentEntityType,
    entity_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
):
    context = await comment_service.resolve_entity_context(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    await get_project_membership_for_user(db, context.project_id, user)
    comments = await comment_service.list_comments(
        db,
        context=context,
    )
    return CommentListResponse(data=comments)


@router.post("", response_model=CommentItem, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    context = await comment_service.resolve_entity_context(
        db,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
    )
    access = await get_project_membership_for_user(db, context.project_id, user)
    check_role_name(access.role_name, "owner", "manager", "member")

    comment = await comment_service.create_comment(
        db,
        context=context,
        author=user,
        content=body.content,
        parent_comment_id=body.parent_comment_id,
        activity_context=activity_log_service.activity_context_from_request(
            user, request
        ),
    )
    comment = await comment_service.get_comment_by_id(db, comment_id=comment.id)
    if comment is None:
        raise NotFoundError("Comment not found")
    return comment_service.to_comment_item(comment)


@router.patch("/{comment_id}", response_model=CommentItem)
async def update_comment(
    comment_id: UUID,
    body: CommentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    comment = await comment_service.get_comment_by_id(db, comment_id=comment_id)
    if comment is None:
        raise NotFoundError("Comment not found")

    context = await comment_service.resolve_entity_context(
        db,
        entity_type=comment.entity_type,
        entity_id=comment.entity_id,
    )
    access = await get_project_membership_for_user(db, context.project_id, user)
    if comment.author_id != user.id and access.role_name not in {"owner", "manager"}:
        raise PermissionDeniedError("You do not have permission to edit this comment")

    comment = await comment_service.update_comment(
        db,
        comment=comment,
        content=body.content,
        actor_id=user.id,
        activity_context=activity_log_service.activity_context_from_request(
            user, request
        ),
    )
    comment = await comment_service.get_comment_by_id(db, comment_id=comment.id)
    if comment is None:
        raise NotFoundError("Comment not found")
    return comment_service.to_comment_item(comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    comment = await comment_service.get_comment_by_id(db, comment_id=comment_id)
    if comment is None:
        raise NotFoundError("Comment not found")

    context = await comment_service.resolve_entity_context(
        db,
        entity_type=comment.entity_type,
        entity_id=comment.entity_id,
    )
    access = await get_project_membership_for_user(db, context.project_id, user)
    if comment.author_id != user.id and access.role_name not in {"owner", "manager"}:
        raise PermissionDeniedError("You do not have permission to delete this comment")

    await comment_service.soft_delete_comment(
        db,
        comment=comment,
        activity_context=activity_log_service.activity_context_from_request(
            user, request
        ),
    )
