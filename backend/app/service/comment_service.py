"""
Comment business logic.
"""

import re
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidOperationError, NotFoundError
from app.models.comment import Comment
from app.models.enums import AuditAction, CommentEntityType, NotificationType
from app.models.user import User
from app.repository import comment_repo
from app.service import activity_log_service, notification_service, realtime_service
from app.service.activity_log_service import ActivityContext
from app.service.contracts.comment import CommentEntityContext, CommentItemData

MENTION_TOKEN_PATTERN = re.compile(
    r"@\[[^\]]+\]\(user:(?P<user_id>[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\)"
)
COMMENT_MAX_THREAD_DEPTH = 32


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


def to_comment_item_data(comment: Comment) -> CommentItemData:
    entity_type = _coerce_comment_entity_type(comment.entity_type)
    return {
        "id": comment.id,
        "entity_type": entity_type,
        "entity_id": comment.entity_id,
        "author": {
            "id": comment.author.id,
            "full_name": comment.author.full_name,
            "avatar_url": comment.author.avatar_url,
        },
        "content": comment.content,
        "mentions": list(comment.mentions or []),
        "parent_comment_id": comment.parent_comment_id,
        "is_edited": comment.is_edited,
        "edited_at": comment.edited_at,
        "created_at": comment.created_at,
        "replies": [],
    }


async def _validate_reply_parent_chain(
    db: AsyncSession,
    *,
    entity_type: CommentEntityType,
    entity_id: UUID,
    parent_comment_id: UUID,
) -> None:
    depth = 1
    current_parent_id = parent_comment_id
    seen_parent_ids: set[UUID] = set()

    while current_parent_id is not None:
        if current_parent_id in seen_parent_ids:
            raise InvalidOperationError("Comment thread cycle detected")
        seen_parent_ids.add(current_parent_id)

        row = await comment_repo.get_parent_chain_row_for_update(
            db,
            comment_id=current_parent_id,
        )
        if row is None:
            raise InvalidOperationError("Parent comment not found for this entity")

        next_parent_id, parent_entity_type, parent_entity_id, parent_is_deleted = row
        if (
            parent_is_deleted
            or _coerce_comment_entity_type(parent_entity_type) != entity_type
            or parent_entity_id != entity_id
        ):
            raise InvalidOperationError("Parent comment not found for this entity")

        if depth >= COMMENT_MAX_THREAD_DEPTH:
            raise InvalidOperationError(
                f"Comment reply depth limit ({COMMENT_MAX_THREAD_DEPTH}) exceeded"
            )

        depth += 1
        current_parent_id = next_parent_id


async def resolve_entity_context(
    db: AsyncSession,
    *,
    entity_type: CommentEntityType,
    entity_id: UUID,
) -> CommentEntityContext:
    if entity_type == "project":
        row = await comment_repo.get_project_context(db, entity_id=entity_id)
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
        row = await comment_repo.get_task_context(db, entity_id=entity_id)
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
        row = await comment_repo.get_resource_context(db, entity_id=entity_id)
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
        row = await comment_repo.get_assignment_context(db, entity_id=entity_id)
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
        project_id = await comment_repo.get_dependency_context(db, entity_id=entity_id)
        if project_id is None:
            raise NotFoundError("Dependency not found")
        return CommentEntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            entity_name="Dependency",
        )

    if entity_type == "project_member":
        row = await comment_repo.get_project_member_context(db, entity_id=entity_id)
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
) -> list[CommentItemData]:
    comments = await comment_repo.list_active_for_entity_with_author(
        db,
        entity_type=context.entity_type,
        entity_id=context.entity_id,
    )
    items_by_id = {comment.id: to_comment_item_data(comment) for comment in comments}
    root_items: list[CommentItemData] = []
    for comment in comments:
        item = items_by_id[comment.id]
        if comment.parent_comment_id is None:
            root_items.append(item)
            continue

        parent_item = items_by_id.get(comment.parent_comment_id)
        if parent_item is None:
            # TODO:(2026-03-08): Add a periodic cleanup job for orphan comments
            # created by historical races/corruption so these rows are healed
            # instead of only being hidden at read time.
            continue
        parent_item["replies"].append(item)

    return root_items


async def get_comment_by_id(
    db: AsyncSession,
    *,
    comment_id: UUID,
) -> Comment | None:
    return await comment_repo.get_active_by_id_with_author(
        db,
        comment_id=comment_id,
    )


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
        await _validate_reply_parent_chain(
            db,
            entity_type=context.entity_type,
            entity_id=context.entity_id,
            parent_comment_id=parent_comment_id,
        )

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
    comments = await comment_repo.list_active_for_entity_for_update(
        db,
        entity_type=comment_entity_type,
        entity_id=comment.entity_id,
    )
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

    owner_id = await comment_repo.get_project_owner_id(db, project_id=project_id)
    if owner_id is None:
        raise NotFoundError("Project not found")

    member_user_ids = await comment_repo.list_project_member_user_ids(
        db,
        project_id=project_id,
    )
    allowed_user_ids = {owner_id, *member_user_ids}
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

    project_name = (
        await comment_repo.get_project_name(db, project_id=project_id) or "Project"
    )
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
