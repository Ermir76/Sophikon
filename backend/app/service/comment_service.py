"""
Comment business logic.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import InvalidOperationError, NotFoundError
from app.models.assignment import Assignment
from app.models.comment import Comment
from app.models.dependency import Dependency
from app.models.enums import AuditAction, NotificationType
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.resource import Resource
from app.models.task import Task
from app.models.user import User
from app.schema.comment import CommentAuthor, CommentEntityType, CommentItem
from app.service import activity_log_service, notification_service, realtime_service
from app.service.activity_log_service import ActivityContext

MENTION_TOKEN_PATTERN = re.compile(
    r"@\[[^\]]+\]\(user:(?P<user_id>[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\)"
)


@dataclass(frozen=True, slots=True)
class CommentEntityContext:
    entity_type: CommentEntityType
    entity_id: UUID
    project_id: UUID
    entity_name: str | None = None


def parse_mention_user_ids(content: str) -> list[UUID]:
    mention_ids: list[UUID] = []
    seen: set[UUID] = set()
    for match in MENTION_TOKEN_PATTERN.finditer(content):
        try:
            user_id = UUID(match.group("user_id"))
        except ValueError:
            continue
        if user_id in seen:
            continue
        seen.add(user_id)
        mention_ids.append(user_id)
    return mention_ids


def _coerce_comment_entity_type(
    entity_type: CommentEntityType | str,
) -> CommentEntityType:
    if isinstance(entity_type, CommentEntityType):
        return entity_type
    try:
        return CommentEntityType(entity_type)
    except ValueError as exc:
        raise InvalidOperationError("Unsupported comment entity type") from exc


def to_comment_item(comment: Comment) -> CommentItem:
    entity_type = _coerce_comment_entity_type(comment.entity_type)
    return CommentItem(
        id=comment.id,
        entity_type=entity_type,
        entity_id=comment.entity_id,
        author=CommentAuthor(
            id=comment.author.id,
            full_name=comment.author.full_name,
            avatar_url=comment.author.avatar_url,
        ),
        content=comment.content,
        mentions=list(comment.mentions or []),
        parent_comment_id=comment.parent_comment_id,
        is_edited=comment.is_edited,
        edited_at=comment.edited_at,
        created_at=comment.created_at,
        replies=[],
    )


async def resolve_entity_context(
    db: AsyncSession,
    *,
    entity_type: CommentEntityType,
    entity_id: UUID,
) -> CommentEntityContext:
    if entity_type == "project":
        result = await db.execute(
            select(Project.id, Project.name).where(
                Project.id == entity_id,
                Project.is_deleted == False,  # noqa: E712
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Project not found")
        project_id, project_name = row
        return CommentEntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            entity_name=project_name,
        )

    if entity_type == "task":
        result = await db.execute(
            select(Task.project_id, Task.name).where(
                Task.id == entity_id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Task not found")
        project_id, task_name = row
        return CommentEntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            entity_name=task_name,
        )

    if entity_type == "resource":
        result = await db.execute(
            select(Resource.project_id, Resource.name).where(Resource.id == entity_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Resource not found")
        project_id, resource_name = row
        return CommentEntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            entity_name=resource_name,
        )

    if entity_type == "assignment":
        result = await db.execute(
            select(Task.project_id, Task.name)
            .join(Assignment, Assignment.task_id == Task.id)
            .where(
                Assignment.id == entity_id,
                Task.is_deleted == False,  # noqa: E712
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Assignment not found")
        project_id, task_name = row
        return CommentEntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            entity_name=task_name,
        )

    if entity_type == "dependency":
        result = await db.execute(
            select(Dependency.project_id).where(Dependency.id == entity_id)
        )
        project_id = result.scalar_one_or_none()
        if project_id is None:
            raise NotFoundError("Dependency not found")
        return CommentEntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            entity_name="Dependency",
        )

    if entity_type == "project_member":
        result = await db.execute(
            select(ProjectMember.project_id, User.full_name)
            .join(User, User.id == ProjectMember.user_id)
            .where(ProjectMember.id == entity_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Project member not found")
        project_id, member_name = row
        return CommentEntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            entity_name=member_name,
        )

    raise InvalidOperationError("Unsupported comment entity type")


async def list_comments(
    db: AsyncSession,
    *,
    context: CommentEntityContext,
) -> list[CommentItem]:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.entity_type == context.entity_type,
            Comment.entity_id == context.entity_id,
            Comment.is_deleted == False,  # noqa: E712
        )
        .order_by(Comment.created_at.asc())
    )
    comments = list(result.scalars().all())
    comment_ids = {comment.id for comment in comments}
    children_map: dict[UUID | None, list[Comment]] = defaultdict(list)
    for comment in comments:
        if (
            comment.parent_comment_id is not None
            and comment.parent_comment_id not in comment_ids
        ):
            # TODO:(2026-03-08): Add a periodic cleanup job for orphan comments
            # created by historical races/corruption so these rows are healed
            # instead of only being hidden at read time.
            continue
        children_map[comment.parent_comment_id].append(comment)

    def _to_item(comment: Comment) -> CommentItem:
        item = to_comment_item(comment)
        item.replies = [_to_item(reply) for reply in children_map.get(comment.id, [])]
        return item

    return [_to_item(comment) for comment in children_map.get(None, [])]


async def get_comment_by_id(
    db: AsyncSession,
    *,
    comment_id: UUID,
) -> Comment | None:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.id == comment_id,
            Comment.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def create_comment(
    db: AsyncSession,
    *,
    context: CommentEntityContext,
    author: User,
    content: str,
    parent_comment_id: UUID | None = None,
    activity_context: ActivityContext | None = None,
) -> Comment:
    mentions = await _resolve_mentions_for_project(db, context.project_id, content)

    if parent_comment_id is not None:
        parent_result = await db.execute(
            select(Comment)
            .where(
                Comment.id == parent_comment_id,
                Comment.entity_type == context.entity_type,
                Comment.entity_id == context.entity_id,
                Comment.is_deleted == False,  # noqa: E712
            )
            .with_for_update()
        )
        if parent_result.scalar_one_or_none() is None:
            raise InvalidOperationError("Parent comment not found for this entity")

    comment = Comment(
        entity_type=context.entity_type,
        entity_id=context.entity_id,
        author_id=author.id,
        content=content,
        parent_comment_id=parent_comment_id,
        mentions=mentions,
    )
    db.add(comment)
    await db.flush()

    await _create_mention_notifications(
        db,
        project_id=context.project_id,
        actor_id=author.id,
        comment=comment,
        mentioned_user_ids=mentions,
    )
    await activity_log_service.log_activity(
        db,
        project_id=context.project_id,
        action=AuditAction.CREATED,
        entity_type="comment",
        entity_id=comment.id,
        entity_name=context.entity_name,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=context.project_id,
        entity_type="comment",
        action=AuditAction.CREATED,
        entity_id=comment.id,
        entity_name=context.entity_name,
        context=activity_context,
        metadata=_comment_event_metadata(comment),
    )
    await realtime_service.commit_and_publish(db)
    await db.refresh(comment)
    return comment


async def update_comment(
    db: AsyncSession,
    *,
    comment: Comment,
    content: str,
    actor_id: UUID,
    activity_context: ActivityContext | None = None,
) -> Comment:
    comment_entity_type = _coerce_comment_entity_type(comment.entity_type)
    context = await resolve_entity_context(
        db,
        entity_type=comment_entity_type,
        entity_id=comment.entity_id,
    )
    before = {
        "content": comment.content,
        "mentions": list(comment.mentions or []),
    }
    mentions = await _resolve_mentions_for_project(db, context.project_id, content)

    changes = activity_log_service.build_change_set(
        before,
        {"content": content, "mentions": mentions},
    )
    if changes is None:
        return comment

    comment.content = content
    comment.mentions = mentions
    comment.is_edited = True
    comment.edited_at = datetime.now(UTC)

    added_mentions = [
        mention for mention in mentions if mention not in set(before["mentions"])
    ]
    await _create_mention_notifications(
        db,
        project_id=context.project_id,
        actor_id=actor_id,
        comment=comment,
        mentioned_user_ids=added_mentions,
    )
    await activity_log_service.log_activity(
        db,
        project_id=context.project_id,
        action=AuditAction.UPDATED,
        entity_type="comment",
        entity_id=comment.id,
        entity_name=context.entity_name,
        changes=changes,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=context.project_id,
        entity_type="comment",
        action=AuditAction.UPDATED,
        entity_id=comment.id,
        entity_name=context.entity_name,
        context=activity_context,
        metadata={
            **_comment_event_metadata(comment),
            "changes": changes,
        },
    )
    await realtime_service.commit_and_publish(db)
    await db.refresh(comment)
    return comment


async def soft_delete_comment(
    db: AsyncSession,
    *,
    comment: Comment,
    activity_context: ActivityContext | None = None,
) -> None:
    comment_entity_type = _coerce_comment_entity_type(comment.entity_type)
    context = await resolve_entity_context(
        db,
        entity_type=comment_entity_type,
        entity_id=comment.entity_id,
    )
    # TODO(2026-03-08): This currently loads and locks all non-deleted comments
    # for the entity to compute a subtree delete. Revisit if comment volumes grow
    # (use recursive SQL/CTE or chunked traversal to reduce lock scope).
    result = await db.execute(
        select(Comment)
        .where(
            Comment.entity_type == comment.entity_type,
            Comment.entity_id == comment.entity_id,
            Comment.is_deleted == False,  # noqa: E712
        )
        .with_for_update()
    )
    comments = list(result.scalars().all())
    by_id = {row.id: row for row in comments}
    children: dict[UUID | None, list[UUID]] = defaultdict(list)
    for row in comments:
        children[row.parent_comment_id].append(row.id)

    stack = [comment.id]
    delete_ids: list[UUID] = []
    while stack:
        current = stack.pop()
        if current not in by_id:
            continue
        delete_ids.append(current)
        stack.extend(children.get(current, []))

    deleted_at = datetime.now(UTC)
    for comment_id in delete_ids:
        row = by_id[comment_id]
        row.is_deleted = True
        row.deleted_at = deleted_at
    await db.flush()

    await activity_log_service.log_activity(
        db,
        project_id=context.project_id,
        action=AuditAction.DELETED,
        entity_type="comment",
        entity_id=comment.id,
        entity_name=context.entity_name,
        context=activity_context,
    )
    realtime_service.queue_entity_event(
        db,
        project_id=context.project_id,
        entity_type="comment",
        action=AuditAction.DELETED,
        entity_id=comment.id,
        entity_name=context.entity_name,
        context=activity_context,
        metadata={
            **_comment_event_metadata(comment),
            "deleted_count": len(delete_ids),
        },
    )
    await realtime_service.commit_and_publish(db)


async def _resolve_mentions_for_project(
    db: AsyncSession,
    project_id: UUID,
    content: str,
) -> list[UUID]:
    mention_ids = parse_mention_user_ids(content)
    if not mention_ids:
        return []

    project_result = await db.execute(
        select(Project.owner_id).where(
            Project.id == project_id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    owner_id = project_result.scalar_one_or_none()
    if owner_id is None:
        raise NotFoundError("Project not found")

    members_result = await db.execute(
        select(ProjectMember.user_id).where(ProjectMember.project_id == project_id)
    )
    allowed_user_ids = {owner_id, *members_result.scalars().all()}
    invalid_user_ids = [
        mention_id for mention_id in mention_ids if mention_id not in allowed_user_ids
    ]
    if invalid_user_ids:
        raise InvalidOperationError("Mentioned user is not a project member")

    return mention_ids


async def _create_mention_notifications(
    db: AsyncSession,
    *,
    project_id: UUID,
    actor_id: UUID,
    comment: Comment,
    mentioned_user_ids: list[UUID],
) -> None:
    if not mentioned_user_ids:
        return

    project_result = await db.execute(
        select(Project.name).where(Project.id == project_id)
    )
    project_name = project_result.scalar_one_or_none() or "Project"
    for user_id in mentioned_user_ids:
        if user_id == actor_id:
            continue
        await notification_service.create_notification(
            db,
            user_id=user_id,
            type=NotificationType.MENTIONED,
            title="You were mentioned in a comment",
            message=f"You were mentioned in {project_name}.",
            entity_type="comment",
            entity_id=comment.id,
            actor_id=actor_id,
        )


def _comment_event_metadata(comment: Comment) -> dict[str, object]:
    return {
        "comment_entity_type": comment.entity_type,
        "comment_entity_id": comment.entity_id,
        "parent_comment_id": comment.parent_comment_id,
        "mentions": list(comment.mentions or []),
    }
