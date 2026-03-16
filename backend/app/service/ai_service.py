import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
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
    ConstraintType,
    DependencyType,
    LagFormat,
    TaskType,
)
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.service import (
    dependency_service,
    project_member_service,
    scheduling_service,
    task_bulk_service,
    task_hierarchy_service,
    task_service,
)
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
    ChatHistoryItem,
    ProjectContext,
    ProjectContextTask,
    ToolResultInput,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Approval store — in-memory, single-server (fine for demo/portfolio)
# ---------------------------------------------------------------------------

_APPROVAL_STORE: dict[str, asyncio.Future] = {}


async def resolve_approval(approval_id: str, approved: bool) -> None:
    future = _APPROVAL_STORE.get(approval_id)
    if future is None or future.done():
        raise NotFoundError("Approval not found or already resolved")
    future.set_result(approved)


async def _wait_for_approval(approval_id: str) -> bool:
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()
    _APPROVAL_STORE[approval_id] = future
    try:
        return await asyncio.wait_for(asyncio.shield(future), timeout=300.0)
    except TimeoutError:
        return False
    finally:
        _APPROVAL_STORE.pop(approval_id, None)


# ---------------------------------------------------------------------------
# AI preferences
# ---------------------------------------------------------------------------

_ALWAYS_APPROVAL_TOOLS = {"delete_task", "delete_dependency"}
_READ_TOOLS = {
    "get_tasks",
    "get_task",
    "search_tasks",
    "get_dependencies",
    "get_critical_path",
    "get_project_summary",
    "get_members",
}
_UI_TOOLS = {"navigate", "highlight_tasks", "open_task", "filter_view"}
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


def _get_auto_approve(user: User, tool_name: str) -> bool:
    prefs = (user.preferences or {}).get("ai", {}).get("auto_approve", {})
    return prefs.get(tool_name, _DEFAULT_AUTO_APPROVE.get(tool_name, True))


def _get_catalog_provider(catalog: dict, provider_id: str | None) -> dict | None:
    if provider_id is None:
        return None
    for provider in catalog.get("providers", []):
        if provider.get("provider_id") == provider_id:
            return provider
    return None


def _recommended_model_id(provider: dict) -> str | None:
    models = provider.get("models", [])
    for model in models:
        if model.get("recommended"):
            return model.get("model_id")
    if models:
        return models[0].get("model_id")
    return None


def _is_valid_model_for_provider(
    catalog: dict, provider_id: str, model_id: str
) -> bool:
    provider = _get_catalog_provider(catalog, provider_id)
    if provider is None:
        return False
    return any(m.get("model_id") == model_id for m in provider.get("models", []))


def _is_provider_available(catalog: dict, provider_id: str) -> bool:
    provider = _get_catalog_provider(catalog, provider_id)
    if provider is None:
        return False
    return bool(provider.get("available", False))


def _read_user_ai_preferences(user: User) -> dict:
    prefs = dict(user.preferences or {})
    return dict(prefs.get("ai", {}))


def _resolve_effective_provider_model(
    user: User, catalog: dict
) -> tuple[str | None, str | None]:
    ai_prefs = _read_user_ai_preferences(user)
    defaults = catalog.get("defaults", {})
    provider = ai_prefs.get("provider") or defaults.get("provider")
    model = ai_prefs.get("model") or defaults.get("model")

    if provider and model and _is_valid_model_for_provider(catalog, provider, model):
        return provider, model
    default_provider = defaults.get("provider")
    if default_provider:
        provider_obj = _get_catalog_provider(catalog, default_provider)
        if provider_obj is not None:
            return default_provider, _recommended_model_id(provider_obj)

    providers = catalog.get("providers", [])
    if providers:
        first_provider = providers[0]
        return first_provider.get("provider_id"), _recommended_model_id(first_provider)
    return None, None


def build_ai_preferences_response(user: User, catalog: dict) -> dict:
    ai_prefs = _read_user_ai_preferences(user)
    auto = dict(ai_prefs.get("auto_approve", {}))
    merged_auto = {**_DEFAULT_AUTO_APPROVE, **auto}
    provider, model = _resolve_effective_provider_model(user, catalog)
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
        provider_obj = _get_catalog_provider(catalog, provider)
        if provider_obj is None:
            raise ValidationError(f"Unsupported AI provider '{provider}'")
        if not _is_provider_available(catalog, provider):
            raise ValidationError(f"Provider '{provider}' is not configured on server")
        if model is None or not _is_valid_model_for_provider(catalog, provider, model):
            if model_patch is not None:
                raise ValidationError(
                    f"Model '{model_patch}' is not valid for provider '{provider}'"
                )
            model = _recommended_model_id(provider_obj)

        if model is None:
            raise ValidationError(f"No models configured for provider '{provider}'")
        if not _is_valid_model_for_provider(catalog, provider, model):
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
# Tool executor — dispatches Claude tool calls to real services
# ---------------------------------------------------------------------------


async def _execute_tool(
    tool_name: str,
    tool_input: dict,
    db: AsyncSession,
    project: Project,
    user: User,
) -> str:
    try:
        result = await _dispatch_tool(tool_name, tool_input, db, project, user)
        return json.dumps(result, default=str)
    except AppException:
        raise
    except Exception as exc:
        logger.exception("Tool execution error: %s", tool_name)
        raise InvalidOperationError(f"Tool '{tool_name}' failed: {exc}") from exc


async def _dispatch_tool(
    tool_name: str,
    tool_input: dict,
    db: AsyncSession,
    project: Project,
    user: User,
) -> object:
    # --- Read tools ---
    if tool_name == "get_tasks":
        filter_status = tool_input.get("filter_status", "all")
        today = date.today()
        tasks, _ = await task_service.list_tasks(db, project, per_page=250)
        result = []
        for t in tasks:
            if filter_status == "overdue" and not (
                float(t.percent_complete) < 100 and t.finish_date < today
            ):
                continue
            if filter_status == "in_progress" and not (
                0 < float(t.percent_complete) < 100
            ):
                continue
            if filter_status == "completed" and not float(t.percent_complete) >= 100:
                continue
            if filter_status == "not_started" and not float(t.percent_complete) == 0:
                continue
            result.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "wbs_code": t.wbs_code,
                    "start_date": str(t.start_date),
                    "finish_date": str(t.finish_date),
                    "duration": t.duration,
                    "percent_complete": float(t.percent_complete),
                    "priority": t.priority,
                    "is_summary": t.is_summary,
                    "is_critical": t.is_critical,
                    "notes": t.notes,
                }
            )
        return {"tasks": result, "total": len(result)}

    if tool_name == "get_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        return {
            "id": str(task.id),
            "name": task.name,
            "wbs_code": task.wbs_code,
            "start_date": str(task.start_date),
            "finish_date": str(task.finish_date),
            "duration": task.duration,
            "percent_complete": float(task.percent_complete),
            "priority": task.priority,
            "is_summary": task.is_summary,
            "is_critical": task.is_critical,
            "notes": task.notes,
            "parent_task_id": str(task.parent_task_id) if task.parent_task_id else None,
        }

    if tool_name == "search_tasks":
        query = (tool_input.get("query") or "").lower()
        overdue_only = tool_input.get("overdue_only", False)
        in_progress_only = tool_input.get("in_progress_only", False)
        today = date.today()
        tasks, _ = await task_service.list_tasks(db, project, per_page=250)
        results = []
        for t in tasks:
            if (
                query
                and query not in (t.name or "").lower()
                and query not in (t.notes or "").lower()
            ):
                continue
            pct = float(t.percent_complete)
            if overdue_only and not (pct < 100 and t.finish_date < today):
                continue
            if in_progress_only and not (0 < pct < 100):
                continue
            results.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "percent_complete": pct,
                    "finish_date": str(t.finish_date),
                    "is_critical": t.is_critical,
                }
            )
        return {"tasks": results, "count": len(results)}

    if tool_name == "get_dependencies":
        deps, _ = await dependency_service.list_dependencies(db, project, per_page=500)
        return {
            "dependencies": [
                {
                    "id": str(d.id),
                    "predecessor_id": str(d.predecessor_id),
                    "successor_id": str(d.successor_id),
                    "type": d.type,
                }
                for d in deps
            ]
        }

    if tool_name == "get_critical_path":
        tasks = await scheduling_service.get_critical_path_tasks(db, project)
        return {
            "critical_path": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "start_date": str(t.start_date),
                    "finish_date": str(t.finish_date),
                    "duration": t.duration,
                }
                for t in tasks
            ]
        }

    if tool_name == "get_project_summary":
        ctx = await build_project_context(db, project)
        today = date.today()
        total = len(ctx.tasks)
        overdue = sum(
            1 for t in ctx.tasks if t.percent_complete < 100 and t.finish_date < today
        )
        in_progress = sum(1 for t in ctx.tasks if 0 < t.percent_complete < 100)
        completed = sum(1 for t in ctx.tasks if t.percent_complete >= 100)
        return {
            "name": ctx.name,
            "status": ctx.status,
            "start_date": str(ctx.start_date),
            "finish_date": str(ctx.finish_date) if ctx.finish_date else None,
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "overdue": overdue,
        }

    if tool_name == "get_members":
        members, _ = await project_member_service.list_members(
            db, project, per_page=100
        )
        return {"members": members}

    # --- Write tools ---
    if tool_name == "create_task":
        payload = {
            "name": tool_input["name"],
            "start_date": date.fromisoformat(tool_input["start_date"]),
            "duration": int(tool_input["duration"]),
            "parent_task_id": UUID(tool_input["parent_task_id"])
            if tool_input.get("parent_task_id")
            else None,
            "notes": tool_input.get("notes"),
            "is_milestone": False,
            "task_type": TaskType.STANDARD,
            "effort_driven": False,
            "constraint_type": ConstraintType.ASAP,
            "constraint_date": None,
            "deadline": None,
            "priority": 0,
            "fixed_cost": Decimal("0"),
            "calendar_id": None,
            "color": None,
        }
        task = await task_service.create_task(db, project, payload)
        return {
            "created": {
                "id": str(task.id),
                "name": task.name,
                "wbs_code": task.wbs_code,
            }
        }

    if tool_name == "update_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        patch = {
            k: v for k, v in tool_input.items() if k != "task_id" and v is not None
        }
        if "start_date" in patch:
            patch["start_date"] = date.fromisoformat(patch["start_date"])
        if "percent_complete" in patch:
            patch["percent_complete"] = Decimal(str(patch["percent_complete"]))
        updated = await task_service.update_task(db, task, patch, project=project)
        return {"updated": {"id": str(updated.id), "name": updated.name}}

    if tool_name == "bulk_create_tasks":
        from app.service.contracts.task_bulk import TaskCreateInput

        items: list[TaskCreateInput] = []
        for t in tool_input.get("tasks", []):
            items.append(
                {
                    "name": t["name"],
                    "start_date": date.fromisoformat(t["start_date"]),
                    "duration": int(t["duration"]),
                    "parent_task_id": None,
                    "notes": t.get("notes"),
                    "is_milestone": False,
                    "task_type": TaskType.STANDARD,
                    "effort_driven": False,
                    "constraint_type": ConstraintType.ASAP,
                    "constraint_date": None,
                    "deadline": None,
                    "priority": 0,
                    "fixed_cost": Decimal("0"),
                    "calendar_id": None,
                    "color": None,
                }
            )
        created, _ = await task_bulk_service.bulk_create_tasks(db, project, items)
        return {
            "created_count": len(created),
            "tasks": [{"id": str(t.id), "name": t.name} for t in created],
        }

    if tool_name == "add_dependency":
        from app.service.contracts.dependency import DependencyCreateInput

        payload: DependencyCreateInput = {
            "predecessor_id": UUID(tool_input["predecessor_id"]),
            "successor_id": UUID(tool_input["successor_id"]),
            "type": DependencyType(tool_input.get("type", "FS")),
            "lag": 0,
            "lag_format": LagFormat.DURATION,
        }
        dep = await dependency_service.create_dependency(db, project, payload)
        return {"created": {"id": str(dep.id), "type": str(dep.type)}}

    if tool_name == "indent_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        updated = await task_hierarchy_service.indent_task(db, project, task)
        return {
            "indented": {
                "id": str(updated.id),
                "name": updated.name,
                "wbs_code": updated.wbs_code,
            }
        }

    if tool_name == "outdent_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        updated = await task_hierarchy_service.outdent_task(db, project, task)
        return {
            "outdented": {
                "id": str(updated.id),
                "name": updated.name,
                "wbs_code": updated.wbs_code,
            }
        }

    if tool_name == "reorder_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        after_id = (
            UUID(tool_input["after_task_id"])
            if tool_input.get("after_task_id")
            else None
        )
        before_id = (
            UUID(tool_input["before_task_id"])
            if tool_input.get("before_task_id")
            else None
        )
        new_parent = (
            UUID(tool_input["new_parent_id"])
            if tool_input.get("new_parent_id")
            else None
        )
        updated = await task_hierarchy_service.reorder_task(
            db, project, task, after_id, before_id, new_parent
        )
        return {"reordered": {"id": str(updated.id), "name": updated.name}}

    if tool_name == "calculate_schedule":
        result = await scheduling_service.calculate_schedule(db, project)
        await db.commit()
        return {
            "scheduled": True,
            "tasks_updated": result.tasks_updated,
            "critical_path_tasks": len(result.critical_path_task_ids),
            "project_finish_date": str(result.project_finish_date)
            if result.project_finish_date
            else None,
        }

    # --- Destructive tools ---
    if tool_name == "delete_task":
        task_id = UUID(tool_input["task_id"])
        task = await task_service.get_task_by_id(db, task_id, project.id)
        if not task:
            return {"error": "Task not found"}
        await task_service.soft_delete_task(db, task, project=project)
        await db.commit()
        return {"deleted": {"id": str(task_id), "name": task.name}}

    if tool_name == "delete_dependency":
        dep_id = UUID(tool_input["dependency_id"])
        dep = await dependency_service.get_dependency_by_id(db, dep_id, project.id)
        if not dep:
            return {"error": "Dependency not found"}
        await dependency_service.delete_dependency(db, dep, project=project)
        return {"deleted": {"id": str(dep_id)}}

    # --- UI tools (no-op on backend — frontend handles the action via SSE event) ---
    if tool_name in _UI_TOOLS:
        return {"action": tool_name, "payload": tool_input, "status": "dispatched"}

    return {"error": f"Unknown tool: {tool_name}"}


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


# ---------------------------------------------------------------------------
# AI-service HTTP streaming
# ---------------------------------------------------------------------------


async def _stream_from_service(
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


# ---------------------------------------------------------------------------
# Agentic loop — multi-turn orchestration
# ---------------------------------------------------------------------------

_MAX_AGENTIC_ITERATIONS = 10


async def prepare_chat_stream(
    db: AsyncSession,
    *,
    project: Project,
    user: User,
    body: AIChatInput,
) -> AsyncGenerator[str]:
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

    async def _stream():
        selected_provider: str | None = None
        selected_model: str | None = None
        context: ProjectContext | None = None
        history: list[ChatHistoryItem] = [
            ChatHistoryItem(role=item.role, content=item.content)
            for item in body.history
        ]
        current_message: str | None = body.message
        current_tool_results: list[ToolResultInput] = []
        accumulated_text: list[str] = []
        total_usage = AIUsageMeta()
        model: str | None = None

        try:
            context = await build_project_context(db, project)
            catalog = await get_model_catalog()
            selected_provider, selected_model = _resolve_effective_provider_model(
                user, catalog
            )

            for iteration in range(_MAX_AGENTIC_ITERATIONS):
                service_request = AIProviderChatRequest(
                    message=current_message,
                    provider=selected_provider,
                    model=selected_model,
                    project_context=context,
                    conversation_id=conversation.id,
                    user_id=user.id,
                    ui_context=body.ui_context,
                    history=history,
                    tool_results=current_tool_results,
                )

                tool_calls: list[AIChatEvent] = []
                turn_text_chunks: list[str] = []

                async for event in _stream_from_service(service_request):
                    if event.type == "start" and iteration == 0:
                        event.conversation_id = conversation.id
                        yield _format_sse_event(event)

                    elif event.type == "chunk" and event.content:
                        turn_text_chunks.append(event.content)
                        accumulated_text.append(event.content)
                        yield _format_sse_event(event)

                    elif event.type == "tool_call":
                        tool_calls.append(event)
                        yield _format_sse_event(event)

                    elif event.type == "done":
                        if event.usage:
                            total_usage.tokens_in += event.usage.tokens_in
                            total_usage.tokens_out += event.usage.tokens_out
                            total_usage.model = event.usage.model
                        model = event.model or model
                        # Don't yield "done" yet — may have more turns

                    elif event.type == "error":
                        yield _format_sse_event(event)
                        return

                if not tool_calls:
                    # Claude is done — no more tool calls
                    break

                # Build assistant history entry with tool_use blocks
                assistant_content: list[dict] = []
                if turn_text_chunks:
                    assistant_content.append(
                        {"type": "text", "text": "".join(turn_text_chunks)}
                    )
                for tc in tool_calls:
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": tc.tool_use_id,
                            "name": tc.tool_name,
                            "input": tc.tool_input or {},
                        }
                    )
                history.append(
                    ChatHistoryItem(role="assistant", content=assistant_content)
                )

                # Execute tools and collect results
                next_tool_results: list[ToolResultInput] = []
                for tc in tool_calls:
                    tool_name = tc.tool_name or ""
                    needs_approval = (
                        tool_name in _ALWAYS_APPROVAL_TOOLS
                        or not _get_auto_approve(user, tool_name)
                    )

                    if needs_approval:
                        approval_id = str(uuid4())
                        yield _format_sse_event(
                            AIChatEvent(
                                type="approval_required",
                                approval_id=approval_id,
                                tool_use_id=tc.tool_use_id,
                                tool_name=tool_name,
                                tool_input=tc.tool_input,
                            )
                        )
                        approved = await _wait_for_approval(approval_id)
                        if not approved:
                            next_tool_results.append(
                                ToolResultInput(
                                    tool_use_id=tc.tool_use_id or "",
                                    content="User denied this action.",
                                    is_error=True,
                                )
                            )
                            continue

                    try:
                        result_content = await _execute_tool(
                            tool_name, tc.tool_input or {}, db, project, user
                        )
                        yield _format_sse_event(
                            AIChatEvent(
                                type="tool_result",
                                tool_use_id=tc.tool_use_id,
                                tool_name=tool_name,
                                content=result_content,
                            )
                        )
                        if tool_name in _UI_TOOLS:
                            yield _format_sse_event(
                                AIChatEvent(
                                    type="ui_action",
                                    action=tool_name,
                                    tool_input=tc.tool_input,
                                )
                            )
                        next_tool_results.append(
                            ToolResultInput(
                                tool_use_id=tc.tool_use_id or "",
                                content=result_content,
                            )
                        )
                    except AppException as exc:
                        error_content = f"Error: {exc.message}"
                        yield _format_sse_event(
                            AIChatEvent(
                                type="tool_result",
                                tool_use_id=tc.tool_use_id,
                                tool_name=tool_name,
                                content=error_content,
                            )
                        )
                        next_tool_results.append(
                            ToolResultInput(
                                tool_use_id=tc.tool_use_id or "",
                                content=error_content,
                                is_error=True,
                            )
                        )

                # Next iteration: continuation with tool results
                current_message = None
                current_tool_results = next_tool_results

                # Add tool results as a user history item for the next turn
                history.append(
                    ChatHistoryItem(
                        role="user",
                        content=[
                            {
                                "type": "tool_result",
                                "tool_use_id": tr.tool_use_id,
                                "content": tr.content,
                                **({"is_error": True} if tr.is_error else {}),
                            }
                            for tr in next_tool_results
                        ],
                    )
                )
                current_tool_results = []  # ai-service reads from history now

            # Emit final done
            yield _format_sse_event(
                AIChatEvent(
                    type="done",
                    conversation_id=conversation.id,
                    usage=total_usage,
                    model=model,
                )
            )

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
            assistant_text = "".join(accumulated_text).strip()
            try:
                await asyncio.shield(
                    _finalize_chat(
                        conversation_id=conversation.id,
                        assistant_text=assistant_text,
                        model=model,
                        usage=total_usage,
                        user_id=user.id,
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


# ---------------------------------------------------------------------------
# Estimate and suggestions (unchanged)
# ---------------------------------------------------------------------------


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
