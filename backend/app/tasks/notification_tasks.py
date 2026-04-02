"""
Notification-related Celery tasks.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.assignment import Assignment
from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.project import Project
from app.models.resource import Resource
from app.models.task import Task
from app.models.user import User
from app.service import (
    auth_service,
    email_service,
    notification_service,
    realtime_service,
)

VERIFICATION_REMINDER_HOURS = (6, 12)


async def _enqueue_deadline_approaching_notifications_with_db(
    db: AsyncSession,
    *,
    now: datetime | None = None,
) -> int:
    current_time = now or datetime.now(UTC)
    today = current_time.date()
    window_end = (current_time + timedelta(hours=24)).date()
    day_start = datetime(
        year=current_time.year,
        month=current_time.month,
        day=current_time.day,
        tzinfo=UTC,
    )
    day_end = day_start + timedelta(days=1)

    existing_result = await db.execute(
        select(Notification.user_id, Notification.entity_id).where(
            Notification.type == NotificationType.DEADLINE_APPROACHING,
            Notification.entity_type == "task",
            Notification.created_at >= day_start,
            Notification.created_at < day_end,
        )
    )
    dedupe_keys = {
        (user_id, entity_id)
        for user_id, entity_id in existing_result.all()
        if entity_id is not None
    }

    candidates_result = await db.execute(
        select(Resource.user_id, Task.id, Task.name, Project.name)
        .select_from(Assignment)
        .join(Resource, Resource.id == Assignment.resource_id)
        .join(Task, Task.id == Assignment.task_id)
        .join(Project, Project.id == Task.project_id)
        .where(
            Resource.user_id.is_not(None),
            Task.is_deleted == False,  # noqa: E712
            Project.is_deleted == False,  # noqa: E712
            Task.percent_complete < 100,
            Task.finish_date >= today,
            Task.finish_date <= window_end,
        )
        .distinct()
    )
    created_count = 0
    for user_id, task_id, task_name, project_name in candidates_result.all():
        dedupe_key = (user_id, task_id)
        if dedupe_key in dedupe_keys:
            continue
        await notification_service.create_notification(
            db,
            user_id=user_id,
            type=NotificationType.DEADLINE_APPROACHING,
            title="Task deadline approaching",
            message=f"'{task_name}' in {project_name} is due within 24 hours.",
            entity_type="task",
            entity_id=task_id,
            actor_id=None,
        )
        dedupe_keys.add(dedupe_key)
        created_count += 1

    await realtime_service.commit_and_publish(db)
    return created_count


async def enqueue_deadline_approaching_notifications(
    now: datetime | None = None,
    *,
    db: AsyncSession | None = None,
) -> int:
    if db is not None:
        return await _enqueue_deadline_approaching_notifications_with_db(db, now=now)
    async with AsyncSessionLocal() as session:
        return await _enqueue_deadline_approaching_notifications_with_db(
            session,
            now=now,
        )


@shared_task(
    name="app.tasks.notification_tasks.send_deadline_approaching_notifications"
)
def send_deadline_approaching_notifications() -> int:
    return asyncio.run(enqueue_deadline_approaching_notifications())


async def _send_verification_reminder_email_with_db(
    db: AsyncSession,
    *,
    user_id: str,
) -> bool:
    try:
        parsed_user_id = uuid.UUID(user_id)
    except ValueError:
        return False

    result = await db.execute(select(User).where(User.id == parsed_user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or user.email_verified:
        return False
    if auth_service.is_email_verification_grace_expired(user):
        return False

    await email_service.send_verification_email(
        db,
        user.id,
        user.email,
        is_reminder=True,
    )
    return True


async def send_verification_reminder_email(
    *,
    user_id: str,
) -> bool:
    async with AsyncSessionLocal() as session:
        return await _send_verification_reminder_email_with_db(
            session,
            user_id=user_id,
        )


@shared_task(name="app.tasks.notification_tasks.send_verification_reminder_email")
def send_verification_reminder_email_task(user_id: str) -> bool:
    return asyncio.run(send_verification_reminder_email(user_id=user_id))


def schedule_verification_reminder_emails(*, user_id: str) -> None:
    for hours in VERIFICATION_REMINDER_HOURS:
        send_verification_reminder_email_task.apply_async(
            kwargs={"user_id": user_id},
            countdown=hours * 60 * 60,
        )
