"""
Proactive agent Celery task — daily project health check.
"""

import asyncio
import logging
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.ai_conversation import AIConversation
from app.models.enums import CommentEntityType, NotificationType
from app.models.project import Project
from app.models.user import User
from app.service import comment_service, notification_service
from app.service.agent.context import AgentContext
from app.service.agent.loop import ProactiveFindings, run_proactive_analysis
from app.service.ai_service import (
    _read_user_ai_preferences,
    _resolve_effective_provider_model,
    get_model_catalog,
)

logger = logging.getLogger(__name__)


async def _get_active_project_ids(db: AsyncSession) -> list[UUID]:
    result = await db.execute(select(Project.id).where(Project.is_deleted.is_(False)))
    return list(result.scalars().all())


async def _run_proactive_check(db: AsyncSession, project_id: UUID) -> None:
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        return

    owner_result = await db.execute(select(User).where(User.id == project.owner_id))
    owner = owner_result.scalar_one_or_none()
    if not owner:
        return

    catalog = await get_model_catalog()
    provider, model = _resolve_effective_provider_model(owner, catalog)
    api_key = _read_user_ai_preferences(owner).get("api_key") or ""

    conversation = AIConversation(
        project_id=project.id,
        user_id=project.owner_id,
        title=f"Proactive health check — {project.name}"[:120],
        mode="proactive",
    )
    db.add(conversation)
    await db.flush()

    ctx = AgentContext(
        project_id=project.id,
        user_id=project.owner_id,
        conversation_id=conversation.id,
        db=db,
        project=project,
        provider=provider or "mock",
        model=model or "mock",
        api_key=api_key,
    )

    findings: ProactiveFindings = await run_proactive_analysis(ctx)

    if not findings.has_issues:
        await db.commit()
        return

    # Notification is flushed first so create_comment's internal commit_and_publish
    # commits both rows atomically — if notification flush fails, nothing is committed.
    await notification_service.create_notification(
        db,
        user_id=project.owner_id,
        type=NotificationType.AI_AGENT_FINDING,
        title=f"AI Agent found issues in '{project.name}'",
        message=findings.summary[:500],
        entity_type="project",
        entity_id=project.id,
        actor_id=None,
    )

    comment_ctx = await comment_service.resolve_entity_context(
        db, entity_type=CommentEntityType.PROJECT, entity_id=project.id
    )
    await comment_service.create_comment(
        db,
        context=comment_ctx,
        author=owner,
        content=findings.summary,
    )


async def _run_all_health_checks() -> int:
    async with AsyncSessionLocal() as db:
        project_ids = await _get_active_project_ids(db)

    count = 0
    for project_id in project_ids:
        try:
            async with AsyncSessionLocal() as db:
                await _run_proactive_check(db, project_id)
            count += 1
        except Exception:
            logger.exception("Proactive health check failed for project %s", project_id)
    return count


@shared_task(name="app.tasks.agent_monitor.run_daily_project_health_check")
def run_daily_project_health_check() -> int:
    return asyncio.run(_run_all_health_checks())
