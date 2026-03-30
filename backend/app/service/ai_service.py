import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import httpx
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    InvalidOperationError,
    NotFoundError,
    ValidationError,
)
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.ai_usage import AIUsage
from app.models.enums import (
    AIMessageRole,
)
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.service import organization_service
from app.service.agent.utils import (
    get_catalog_provider,
    is_provider_available,
    is_valid_model_for_provider,
    read_user_ai_preferences,
    recommended_model_id,
    resolve_effective_provider_model,
)
from app.service.contracts.ai import (
    AIChatEvent,
    AIChatInput,
    AICompleteRequest,
    AIEstimateInput,
    AIEstimateItem,
    AIEstimateResult,
    AISuggestionItem,
    AISuggestionsResult,
    AIUsageMeta,
    ConversationMessage,
    ConversationSummary,
    ProjectContext,
    ProjectContextTask,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AI preferences
# ---------------------------------------------------------------------------

_DEFAULT_AUTO_APPROVE: dict[str, bool] = {
    "create_task": True,
    "update_task": True,
    "bulk_create_tasks": True,
    "add_dependency": True,
    "indent_task": True,
    "outdent_task": True,
    "reorder_task": True,
    "calculate_schedule": True,
    "navigate": True,
    "highlight_tasks": True,
    "open_task": True,
    "filter_view": True,
}
_ALLOWED_AUTO_APPROVE_TOOLS = set(_DEFAULT_AUTO_APPROVE.keys())

_MODEL_CATALOG_CACHE_TTL = timedelta(seconds=30)
_MODEL_CATALOG_CACHE: dict | None = None
_MODEL_CATALOG_CACHE_EXPIRES_AT: datetime | None = None


def build_ai_preferences_response(user: User, catalog: dict) -> dict:
    ai_prefs = read_user_ai_preferences(user)
    auto = dict(ai_prefs.get("auto_approve", {}))
    merged_auto = {**_DEFAULT_AUTO_APPROVE, **auto}
    provider, model = resolve_effective_provider_model(user, catalog)
    return {
        "auto_approve": merged_auto,
        "provider": provider,
        "model": model,
        "providers": catalog.get("providers", []),
        "defaults": catalog.get("defaults"),
    }


def apply_ai_preferences_patch(
    *,
    user: User,
    catalog: dict,
    auto_approve_patch: dict[str, bool],
    provider_patch: str | None,
    model_patch: str | None,
) -> dict:
    unknown_auto_approve_keys = sorted(
        set(auto_approve_patch.keys()) - _ALLOWED_AUTO_APPROVE_TOOLS
    )
    if unknown_auto_approve_keys:
        quoted = ", ".join(f"'{key}'" for key in unknown_auto_approve_keys)
        raise ValidationError(f"Unsupported auto_approve keys: {quoted}")

    root = dict(user.preferences or {})
    ai = dict(root.get("ai", {}))
    auto_current = dict(ai.get("auto_approve", {}))
    auto_current.update(auto_approve_patch)
    ai["auto_approve"] = auto_current

    defaults = catalog.get("defaults", {})
    provider = provider_patch if provider_patch is not None else ai.get("provider")
    model = model_patch if model_patch is not None else ai.get("model")
    if provider is None:
        provider = defaults.get("provider")
    if provider:
        provider_obj = get_catalog_provider(catalog, provider)
        if provider_obj is None:
            raise ValidationError(f"Unsupported AI provider '{provider}'")
        if not is_provider_available(catalog, provider):
            raise ValidationError(f"Provider '{provider}' is not configured on server")
        if model is None or not is_valid_model_for_provider(catalog, provider, model):
            if model_patch is not None:
                raise ValidationError(
                    f"Model '{model_patch}' is not valid for provider '{provider}'"
                )
            model = recommended_model_id(provider_obj)

        if model is None:
            raise ValidationError(f"No models configured for provider '{provider}'")
        if not is_valid_model_for_provider(catalog, provider, model):
            raise ValidationError(
                f"Model '{model}' is not valid for provider '{provider}'"
            )

    ai["provider"] = provider
    ai["model"] = model
    root["ai"] = ai
    return root


async def get_model_catalog(*, force_refresh: bool = False) -> dict:
    global _MODEL_CATALOG_CACHE, _MODEL_CATALOG_CACHE_EXPIRES_AT
    now = datetime.now(UTC)
    if (
        not force_refresh
        and _MODEL_CATALOG_CACHE is not None
        and _MODEL_CATALOG_CACHE_EXPIRES_AT is not None
        and now < _MODEL_CATALOG_CACHE_EXPIRES_AT
    ):
        return _MODEL_CATALOG_CACHE

    try:
        async with httpx.AsyncClient(timeout=_request_timeout()) as client:
            response = await client.get(
                _service_url("/v1/brain/models"),
                headers=_service_headers(),
            )
    except httpx.RequestError as exc:
        raise InvalidOperationError("AI service is unavailable") from exc

    if response.status_code >= 400:
        raise InvalidOperationError(await _extract_error_message(response))

    data = response.json()
    _MODEL_CATALOG_CACHE = data
    _MODEL_CATALOG_CACHE_EXPIRES_AT = now + _MODEL_CATALOG_CACHE_TTL
    return data


# ---------------------------------------------------------------------------
# Service helpers
# ---------------------------------------------------------------------------


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


def _format_sse_event(event: AIChatEvent) -> str:
    payload = event.model_dump(mode="json", exclude_none=True)
    return f"data: {json.dumps(payload)}\n\n"


# ---------------------------------------------------------------------------
# Project context builder
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Conversation helpers
# ---------------------------------------------------------------------------


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


async def list_conversations(
    db: AsyncSession,
    *,
    project_id: UUID,
    user_id: UUID,
    limit: int = 20,
) -> list[ConversationSummary]:
    result = await db.execute(
        select(AIConversation)
        .where(
            AIConversation.project_id == project_id,
            AIConversation.user_id == user_id,
        )
        .order_by(AIConversation.updated_at.desc())
        .limit(limit)
    )
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            status=c.status,
            mode=c.mode,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in result.scalars().all()
    ]


async def get_conversation_messages(
    db: AsyncSession,
    *,
    conversation_id: UUID,
    project_id: UUID,
    user_id: UUID,
) -> tuple[ConversationSummary, list[ConversationMessage]]:
    conv_result = await db.execute(
        select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.project_id == project_id,
            AIConversation.user_id == user_id,
        )
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")

    msg_result = await db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at.asc())
    )
    messages = [
        ConversationMessage(
            id=m.id,
            role=str(m.role),
            content=m.content or "",
            created_at=m.created_at,
        )
        for m in msg_result.scalars().all()
    ]
    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        mode=conversation.mode,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    ), messages


# ---------------------------------------------------------------------------
# AI-service HTTP streaming
# ---------------------------------------------------------------------------


_STREAM_MAX_RETRIES = 2
_STREAM_RETRY_BACKOFF = (2.0, 5.0)


async def complete_from_service(
    body: AICompleteRequest,
) -> AsyncGenerator[AIChatEvent]:
    last_exc: Exception | None = None

    for attempt in range(_STREAM_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=_request_timeout()) as client:
                async with client.stream(
                    "POST",
                    _service_url("/v1/complete"),
                    headers=_service_headers(),
                    json=body.model_dump(mode="json"),
                ) as response:
                    if response.status_code >= 400:
                        raise InvalidOperationError(
                            await _extract_error_message(response)
                        )

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
                                type="error", message="Malformed AI stream event"
                            )
                    return  # stream completed successfully
        except httpx.ReadTimeout as exc:
            last_exc = exc
            if attempt < _STREAM_MAX_RETRIES:
                delay = _STREAM_RETRY_BACKOFF[
                    min(attempt, len(_STREAM_RETRY_BACKOFF) - 1)
                ]
                logger.warning(
                    "ReadTimeout on attempt %d/%d, retrying in %.1fs",
                    attempt + 1,
                    _STREAM_MAX_RETRIES + 1,
                    delay,
                )
                await asyncio.sleep(delay)
                continue
        except httpx.RequestError as exc:
            last_exc = exc
            break  # non-timeout network errors are not retryable

    raise InvalidOperationError("AI service is unavailable") from last_exc


# ---------------------------------------------------------------------------
# Agentic loop — multi-turn orchestration
# ---------------------------------------------------------------------------


async def prepare_chat_stream(
    db: AsyncSession,
    *,
    project: Project,
    user: User,
    role_name: str,
    body: AIChatInput,
) -> AsyncGenerator[str]:
    from app.service.agent.context import AgentContext
    from app.service.agent.loop import run_agent

    project_agent_enabled = bool((project.settings or {}).get("agent_enabled", True))
    if not project_agent_enabled:
        raise InvalidOperationError(
            "AI agent is disabled for this project. Enable it in project settings to continue."
        )

    organization = await organization_service.get_organization_by_id(
        db, org_id=project.organization_id
    )
    organization_settings = organization.settings if organization else {}
    org_agent_enabled = bool(organization_settings.get("agent_enabled", True))
    if not org_agent_enabled:
        raise InvalidOperationError(
            "AI agent is disabled for this organization. Contact an organization owner."
        )

    conversation = await get_or_create_conversation(
        db,
        project_id=project.id,
        user_id=user.id,
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

    try:
        catalog = await get_model_catalog()
    except AppException as exc:
        from app.service.agent.streaming import event_error

        _err_msg = exc.message

        async def _catalog_error() -> AsyncGenerator[str]:
            yield event_error(_err_msg)

        return _catalog_error()

    provider, model = resolve_effective_provider_model(user, catalog)
    api_key = read_user_ai_preferences(user).get("api_key") or ""

    ctx = AgentContext(
        project_id=project.id,
        user_id=user.id,
        role_name=role_name,
        conversation_id=conversation.id,
        db=db,
        project=project,
        provider=provider or "mock",
        model=model or "mock",
        api_key=api_key,
    )

    return await run_agent(ctx, body.message)


# ---------------------------------------------------------------------------
# Estimate and suggestions
# ---------------------------------------------------------------------------


def _strip_code_fence(text: str) -> str:
    # NOTE: split("```") breaks if the LLM returns JSON with triple backticks inside
    # string values — the split produces extra parts and inner picks the wrong segment.
    # Low probability in practice (LLMs rarely embed ``` in JSON values) but not impossible.
    # TODO: replace with a regex that matches only the outer fence, e.g.
    #       re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if text.startswith("```"):
        parts = text.split("```")
        inner = parts[1] if len(parts) > 1 else ""
        if inner.startswith("json"):
            inner = inner[4:]
        return inner.strip()
    return text


async def estimate_for_project(
    db: AsyncSession,
    *,
    project: Project,
    user: User,
    body: AIEstimateInput,
) -> AIEstimateResult:
    task_entries: list[dict] = []
    if body.task_ids:
        result = await db.execute(
            select(Task).where(
                Task.project_id == project.id,
                Task.is_deleted.is_(False),
                Task.id.in_(body.task_ids),
            )
        )
        tasks = list(result.scalars().all())
        found_ids = {task.id for task in tasks}
        missing = [tid for tid in body.task_ids if tid not in found_ids]
        if missing:
            raise NotFoundError("One or more tasks were not found in this project")
        task_entries = [
            {
                "task_id": str(task.id),
                "task_name": task.name,
                "description": task.notes or "",
                "current_duration_minutes": task.duration,
            }
            for task in tasks
        ]
    elif body.task_name:
        task_entries = [
            {
                "task_id": None,
                "task_name": body.task_name,
                "description": body.task_description or "",
                "current_duration_minutes": None,
            }
        ]

    if not task_entries:
        raise InvalidOperationError("No tasks to estimate")

    context = await build_project_context(db, project)
    catalog = await get_model_catalog()
    provider, model = resolve_effective_provider_model(user, catalog)
    api_key = read_user_ai_preferences(user).get("api_key") or ""

    project_snapshot = "\n".join(
        f"- {t.name}: {t.duration}min, {int(t.percent_complete)}% done"
        for t in context.tasks[:30]
    )
    task_list = "\n".join(
        f"- {e['task_name']} (id:{e['task_id'] or 'new'}, "
        f"description:{e['description']!r}, "
        f"current:{e['current_duration_minutes']}min)"
        for e in task_entries
    )
    prompt = (
        f"Project: {context.name} (status: {context.status})\n"
        f"Start: {context.start_date}, Finish: {context.finish_date or 'TBD'}\n\n"
        f"Existing tasks (context):\n{project_snapshot}\n\n"
        f"Tasks to estimate:\n{task_list}\n\n"
        f"include_reasoning: {body.include_reasoning}"
    )
    system_prompt = (
        "You are a project estimation expert. For each task, estimate durations in minutes. "
        "Return ONLY valid JSON matching this exact schema (no markdown, no explanation):\n"
        '{"estimates": [{"task_id": "uuid-or-null", "task_name": "str", '
        '"optimistic_minutes": int, "likely_minutes": int, "pessimistic_minutes": int, '
        '"recommended_minutes": int, "confidence": float, "reasoning": "str-or-null"}]}'
    )

    request = AICompleteRequest(
        messages=[{"role": "user", "content": prompt}],
        tools=[],
        system_prompt=system_prompt,
        provider=provider or "mock",
        model=model or "mock",
        api_key=api_key or None,
    )
    text_chunks: list[str] = []
    tokens_in = 0
    tokens_out = 0
    async for event in complete_from_service(request):
        if event.type == "chunk" and event.content:
            text_chunks.append(event.content)
        elif event.type == "done" and event.usage:
            tokens_in = event.usage.tokens_in
            tokens_out = event.usage.tokens_out

    try:
        raw = json.loads(_strip_code_fence("".join(text_chunks).strip()))
        response = AIEstimateResult(
            estimates=[
                AIEstimateItem.model_validate(e) for e in raw.get("estimates", [])
            ],
            usage=AIUsageMeta(tokens_in=tokens_in, tokens_out=tokens_out, model=model),
        )
    except (ValueError, TypeError, PydanticValidationError) as exc:
        raise InvalidOperationError("Malformed AI estimation response") from exc

    usage_meta = response.usage
    await track_usage(db, user_id=user.id, feature="estimation", usage=usage_meta)
    await db.commit()
    return response


async def suggestions_for_project(
    db: AsyncSession,
    *,
    project: Project,
    user: User,
    limit: int,
) -> AISuggestionsResult:
    context = await build_project_context(db, project)
    catalog = await get_model_catalog()
    provider, model = resolve_effective_provider_model(user, catalog)
    api_key = read_user_ai_preferences(user).get("api_key") or ""

    project_snapshot = "\n".join(
        f"- {t.name}: start={t.start_date}, finish={t.finish_date}, "
        f"duration={t.duration}min, {int(t.percent_complete)}% done, priority={t.priority}"
        for t in context.tasks[:50]
    )
    prompt = (
        f"Project: {context.name} (status: {context.status})\n"
        f"Start: {context.start_date}, Finish: {context.finish_date or 'TBD'}\n\n"
        f"Tasks:\n{project_snapshot}\n\n"
        f"Provide up to {limit} actionable suggestions to improve this project schedule."
    )
    action_schema = (
        '{"type":"NONE","payload":{}}'
        ' | {"type":"UPDATE_TASK","payload":{"task_id":"uuid","percent_complete":null,'
        '"duration":null,"priority":null,"notes":null}}'
        ' | {"type":"ADD_DEPENDENCY","payload":{"predecessor_id":"uuid","successor_id":"uuid",'
        '"dependency_type":"FS","lag":0}}'
        ' | {"type":"SET_PRIORITY","payload":{"task_id":"uuid","priority":int}}'
    )
    system_prompt = (
        "You are a project management expert. Analyze the project and suggest improvements. "
        "Return ONLY valid JSON (no markdown, no explanation) matching this exact schema:\n"
        '{"suggestions": [{"id": "unique-str", "type": "str", "severity": "LOW|MEDIUM|HIGH", '
        '"title": "str", "description": "str", "affected_task_id": "uuid-or-null", '
        f'"suggested_action": {action_schema}}}]}}'
    )

    request = AICompleteRequest(
        messages=[{"role": "user", "content": prompt}],
        tools=[],
        system_prompt=system_prompt,
        provider=provider or "mock",
        model=model or "mock",
        api_key=api_key or None,
    )
    text_chunks: list[str] = []
    tokens_in = 0
    tokens_out = 0
    async for event in complete_from_service(request):
        if event.type == "chunk" and event.content:
            text_chunks.append(event.content)
        elif event.type == "done" and event.usage:
            tokens_in = event.usage.tokens_in
            tokens_out = event.usage.tokens_out

    try:
        raw = json.loads(_strip_code_fence("".join(text_chunks).strip()))
        response = AISuggestionsResult(
            suggestions=[
                AISuggestionItem.model_validate(s)
                for s in raw.get("suggestions", [])[:limit]
            ],
            usage=AIUsageMeta(tokens_in=tokens_in, tokens_out=tokens_out, model=model),
        )
    except (ValueError, TypeError, PydanticValidationError) as exc:
        raise InvalidOperationError("Malformed AI suggestions response") from exc

    usage_meta = response.usage
    await track_usage(db, user_id=user.id, feature="suggestion", usage=usage_meta)
    await db.commit()
    return response
