import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import AppException, InvalidOperationError, NotFoundError
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.ai_usage import AIUsage
from app.models.enums import AIMessageRole
from app.models.project import Project
from app.models.task import Task
from app.service.contracts.ai import (
    AIChatEvent,
    AIChatInput,
    AIEstimateInput,
    AIEstimateResult,
    AIProviderChatRequest,
    AIProviderEstimateRequest,
    AIProviderEstimateTaskInput,
    AIProviderSuggestionsRequest,
    AISuggestionsResult,
    AIUsageMeta,
    ProjectContext,
    ProjectContextTask,
)

logger = logging.getLogger(__name__)


def _service_url(path: str) -> str:
    return f"{settings.AI_SERVICE_URL.rstrip('/')}{path}"


def _service_headers() -> dict[str, str]:
    return {"X-AI-Service-Secret": settings.AI_SERVICE_SHARED_SECRET}


def _request_timeout() -> httpx.Timeout:
    return httpx.Timeout(
        timeout=settings.AI_SERVICE_TIMEOUT_SECONDS,
        connect=5.0,
        read=settings.AI_SERVICE_TIMEOUT_SECONDS,
    )


async def _extract_error_message(response: httpx.Response) -> str:
    try:
        raw = await response.aread()
        if not raw:
            return f"AI service error ({response.status_code})"

        payload = json.loads(raw.decode("utf-8"))
        if isinstance(payload, dict):
            if isinstance(payload.get("detail"), str):
                return payload["detail"]
            if isinstance(payload.get("error"), str):
                return payload["error"]
    except Exception:
        pass
    return f"AI service error ({response.status_code})"


def _estimate_cost(tokens_in: int, tokens_out: int) -> Decimal:
    tokens_total = max(tokens_in + tokens_out, 0)
    return Decimal(tokens_total) * Decimal("0.0000005")


async def build_project_context(
    db: AsyncSession,
    project: Project,
    *,
    task_limit: int = 250,
) -> ProjectContext:
    task_result = await db.execute(
        select(Task)
        .where(Task.project_id == project.id, Task.is_deleted.is_(False))
        .order_by(Task.sort_order.asc())
        .limit(task_limit)
    )
    tasks = list(task_result.scalars().all())

    return ProjectContext(
        project_id=project.id,
        name=project.name,
        description=project.description,
        status=str(project.status),
        start_date=project.start_date,
        finish_date=project.finish_date,
        updated_at=project.updated_at,
        tasks=[
            ProjectContextTask(
                id=task.id,
                name=task.name,
                notes=task.notes,
                start_date=task.start_date,
                finish_date=task.finish_date,
                duration=task.duration,
                percent_complete=float(task.percent_complete),
                priority=task.priority,
                is_summary=task.is_summary,
                updated_at=task.updated_at,
            )
            for task in tasks
        ],
    )


async def get_or_create_conversation(
    db: AsyncSession,
    *,
    project_id: UUID,
    user_id: UUID,
    conversation_id: UUID | None,
    initial_title: str,
) -> AIConversation:
    if conversation_id:
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conversation_id,
                AIConversation.project_id == project_id,
                AIConversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise NotFoundError("Conversation not found")
        return conversation

    conversation = AIConversation(
        project_id=project_id,
        user_id=user_id,
        title=initial_title.strip()[:120] or "New conversation",
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def append_message(
    db: AsyncSession,
    *,
    conversation: AIConversation,
    role: AIMessageRole,
    content: str,
    model: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    finish_reason: str | None = None,
) -> AIMessage:
    conversation.updated_at = datetime.now(UTC)
    message = AIMessage(
        conversation_id=conversation.id,
        role=role,
        content=content,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        finish_reason=finish_reason,
    )
    db.add(message)
    await db.flush()
    return message


async def track_usage(
    db: AsyncSession,
    *,
    user_id: UUID,
    feature: str,
    usage: AIUsageMeta | None,
) -> None:
    if usage is None:
        return

    tokens_in = usage.tokens_in or 0
    tokens_out = usage.tokens_out or 0

    record = AIUsage(
        user_id=user_id,
        feature=feature,
        model=usage.model or "unknown",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        estimated_cost=_estimate_cost(tokens_in, tokens_out),
        usage_date=date.today(),
    )
    db.add(record)
    await db.flush()


async def stream_chat(
    body: AIProviderChatRequest,
) -> AsyncGenerator[AIChatEvent]:
    try:
        async with httpx.AsyncClient(timeout=_request_timeout()) as client:
            async with client.stream(
                "POST",
                _service_url("/v1/brain/chat"),
                headers=_service_headers(),
                json=body.model_dump(mode="json"),
            ) as response:
                if response.status_code >= 400:
                    raise InvalidOperationError(await _extract_error_message(response))

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line.removeprefix("data:").strip()
                    if not payload:
                        continue
                    try:
                        parsed = json.loads(payload)
                        yield AIChatEvent.model_validate(parsed)
                    except (ValueError, TypeError):
                        yield AIChatEvent(
                            type="error", error="Malformed AI stream event"
                        )
    except httpx.RequestError:
        raise InvalidOperationError("AI service is unavailable")


async def request_estimate(body: AIProviderEstimateRequest) -> dict:
    try:
        async with httpx.AsyncClient(timeout=_request_timeout()) as client:
            response = await client.post(
                _service_url("/v1/brain/estimate"),
                headers=_service_headers(),
                json=body.model_dump(mode="json"),
            )
        if response.status_code >= 400:
            raise InvalidOperationError(await _extract_error_message(response))
        try:
            return response.json()
        except ValueError as exc:
            raise InvalidOperationError("Malformed AI estimation response") from exc
    except httpx.RequestError:
        raise InvalidOperationError("AI estimation service is unavailable")


async def request_suggestions(body: AIProviderSuggestionsRequest) -> dict:
    try:
        async with httpx.AsyncClient(timeout=_request_timeout()) as client:
            response = await client.post(
                _service_url("/v1/brain/suggestions"),
                headers=_service_headers(),
                json=body.model_dump(mode="json"),
            )
        if response.status_code >= 400:
            raise InvalidOperationError(await _extract_error_message(response))
        try:
            return response.json()
        except ValueError as exc:
            raise InvalidOperationError("Malformed AI suggestions response") from exc
    except httpx.RequestError:
        raise InvalidOperationError("AI suggestions service is unavailable")


def _format_sse_event(event: AIChatEvent) -> str:
    payload = event.model_dump(mode="json", exclude_none=True)
    return f"data: {json.dumps(payload)}\n\n"


async def prepare_chat_stream(
    db: AsyncSession,
    *,
    project: Project,
    user_id: UUID,
    body: AIChatInput,
) -> AsyncGenerator[str]:
    conversation = await get_or_create_conversation(
        db,
        project_id=project.id,
        user_id=user_id,
        conversation_id=body.conversation_id,
        initial_title=body.message,
    )
    await append_message(
        db,
        conversation=conversation,
        role=AIMessageRole.USER,
        content=body.message,
    )
    await db.commit()

    context = await build_project_context(db, project)
    service_request = AIProviderChatRequest(
        message=body.message,
        project_context=context,
        conversation_id=conversation.id,
        user_id=user_id,
        ui_context=body.ui_context,
        history=body.history,
    )

    async def _stream():
        assistant_chunks: list[str] = []
        usage = None
        model = None

        try:
            async for event in stream_chat(service_request):
                if event.type == "start" and event.conversation_id is None:
                    event.conversation_id = conversation.id
                if event.type == "chunk" and event.content:
                    assistant_chunks.append(event.content)
                if event.type == "done":
                    usage = event.usage
                    model = event.model or (usage.model if usage else None)
                yield _format_sse_event(event)
        except AppException as exc:
            yield _format_sse_event(AIChatEvent(type="error", error=exc.message))
        except Exception:
            logger.exception(
                "Unexpected chat streaming failure for conversation %s",
                conversation.id,
            )
            yield _format_sse_event(
                AIChatEvent(type="error", error="AI chat is temporarily unavailable")
            )
        finally:
            assistant_text = "".join(assistant_chunks).strip()
            try:
                await asyncio.shield(
                    _finalize_chat(
                        conversation_id=conversation.id,
                        assistant_text=assistant_text,
                        model=model,
                        usage=usage,
                        user_id=user_id,
                    )
                )
            except asyncio.CancelledError:
                logger.warning(
                    "Chat stream cancelled during finalization for conversation %s",
                    conversation.id,
                )
                raise
            except Exception:
                logger.exception(
                    "Failed to finalize chat persistence for conversation %s",
                    conversation.id,
                )

    return _stream()


async def _finalize_chat(
    *,
    conversation_id: UUID,
    assistant_text: str,
    model: str | None,
    usage: AIUsageMeta | None,
    user_id: UUID,
) -> None:
    try:
        async with AsyncSessionLocal() as finalize_db:
            result = await finalize_db.execute(
                select(AIConversation).where(AIConversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                logger.warning(
                    "Conversation %s not found during chat finalization",
                    conversation_id,
                )
                return

            if assistant_text:
                await append_message(
                    finalize_db,
                    conversation=conversation,
                    role=AIMessageRole.ASSISTANT,
                    content=assistant_text,
                    model=model,
                    tokens_in=usage.tokens_in if usage else None,
                    tokens_out=usage.tokens_out if usage else None,
                    finish_reason="stop",
                )

            await track_usage(
                finalize_db,
                user_id=user_id,
                feature="chat",
                usage=usage,
            )
            await finalize_db.commit()
    except Exception:
        logger.exception(
            "Chat finalization failed for conversation %s",
            conversation_id,
        )


async def _build_estimate_task_inputs(
    db: AsyncSession,
    *,
    project_id: UUID,
    body: AIEstimateInput,
) -> list[AIProviderEstimateTaskInput]:
    task_inputs: list[AIProviderEstimateTaskInput] = []

    if body.task_ids:
        result = await db.execute(
            select(Task).where(
                Task.project_id == project_id,
                Task.is_deleted.is_(False),
                Task.id.in_(body.task_ids),
            )
        )
        tasks = list(result.scalars().all())
        found_ids = {task.id for task in tasks}
        missing_ids = [task_id for task_id in body.task_ids if task_id not in found_ids]
        if missing_ids:
            raise NotFoundError("One or more tasks were not found in this project")

        task_inputs.extend(
            AIProviderEstimateTaskInput(
                task_id=task.id,
                task_name=task.name,
                task_description=task.notes,
                duration=task.duration,
            )
            for task in tasks
        )
    elif body.task_name:
        task_inputs.append(
            AIProviderEstimateTaskInput(
                task_name=body.task_name,
                task_description=body.task_description,
                duration=None,
            )
        )

    return task_inputs


async def estimate_for_project(
    db: AsyncSession,
    *,
    project: Project,
    user_id: UUID,
    body: AIEstimateInput,
) -> AIEstimateResult:
    task_inputs = await _build_estimate_task_inputs(
        db,
        project_id=project.id,
        body=body,
    )
    context = await build_project_context(db, project)
    service_request = AIProviderEstimateRequest(
        project_context=context,
        task_inputs=task_inputs,
        include_reasoning=body.include_reasoning,
    )

    raw_response = await request_estimate(service_request)
    response = AIEstimateResult.model_validate(raw_response)

    await track_usage(
        db,
        user_id=user_id,
        feature="estimation",
        usage=response.usage,
    )
    await db.commit()
    return response


async def suggestions_for_project(
    db: AsyncSession,
    *,
    project: Project,
    user_id: UUID,
    limit: int,
) -> AISuggestionsResult:
    context = await build_project_context(db, project)
    service_request = AIProviderSuggestionsRequest(
        project_context=context,
        limit=limit,
    )

    raw_response = await request_suggestions(service_request)
    response = AISuggestionsResult.model_validate(raw_response)

    await track_usage(
        db,
        user_id=user_id,
        feature="suggestion",
        usage=response.usage,
    )
    await db.commit()
    return response
