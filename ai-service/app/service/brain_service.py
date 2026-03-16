"""AI chat orchestration and deterministic estimate/suggestion helpers."""

from datetime import date
from uuid import uuid4

from app.core.config import settings
from app.schema.contracts import (
    AIUsageMeta,
    ChatEvent,
    ChatRequest,
    EstimateItem,
    EstimateRequest,
    EstimateResponse,
    SuggestionAction,
    SuggestionItem,
    SuggestionsRequest,
    SuggestionsResponse,
)
from app.service.model_catalog import validate_provider_and_model
from app.service.providers.anthropic_provider import stream_claude as _provider_stream_claude
from app.service.providers.common import estimate_tokens
from app.service.providers.gemini_provider import stream_gemini as _provider_stream_gemini
from app.service.providers.mock_provider import stream_mock as _provider_stream_mock
from app.service.providers.openai_provider import stream_openai as _provider_stream_openai
from app.service.providers.tool_catalog import TOOL_DEFINITIONS


def _resolve_runtime_provider_and_model(
    request: ChatRequest,
) -> tuple[str | None, str, str | None]:
    provider, model, error = validate_provider_and_model(request.provider, request.model)
    if settings.AI_MODE != "live":
        return None, model, None
    return provider, model, error


async def _stream_claude(request: ChatRequest, *, model_id: str):
    async for event in _provider_stream_claude(
        request,
        model_id=model_id,
        tool_definitions=TOOL_DEFINITIONS,
    ):
        yield event


async def _stream_openai(request: ChatRequest, *, model_id: str):
    async for event in _provider_stream_openai(
        request,
        model_id=model_id,
        tool_definitions=TOOL_DEFINITIONS,
    ):
        yield event


async def _stream_gemini(request: ChatRequest, *, model_id: str):
    async for event in _provider_stream_gemini(
        request,
        model_id=model_id,
        tool_definitions=TOOL_DEFINITIONS,
    ):
        yield event


async def _stream_mock(request: ChatRequest, *, model_id: str):
    async for event in _provider_stream_mock(request, model_id=model_id):
        yield event


async def stream_chat_events(request: ChatRequest):
    provider, model_id, error = _resolve_runtime_provider_and_model(request)
    if error:
        yield ChatEvent(type="error", error=error, model=model_id).model_dump(
            mode="json", exclude_none=True
        )
        return

    if provider == "anthropic":
        async for event in _stream_claude(request, model_id=model_id):
            yield event
    elif provider == "openai":
        async for event in _stream_openai(request, model_id=model_id):
            yield event
    elif provider == "gemini":
        async for event in _stream_gemini(request, model_id=model_id):
            yield event
    else:
        async for event in _stream_mock(request, model_id=model_id):
            yield event


_KEYWORD_DAY_HINTS: dict[str, float] = {
    "design": 2.0,
    "analysis": 2.0,
    "plan": 1.5,
    "develop": 4.0,
    "implementation": 4.0,
    "integrat": 5.0,
    "api": 3.0,
    "test": 2.5,
    "qa": 2.5,
    "deploy": 2.0,
    "migration": 3.0,
    "security": 3.0,
}


def _base_minutes_from_task_name(task_name: str, original_duration: int | None) -> int:
    if original_duration and original_duration > 0:
        return max(240, original_duration)
    lower_name = task_name.lower()
    matched_days = [days for key, days in _KEYWORD_DAY_HINTS.items() if key in lower_name]
    if matched_days:
        return int(max(matched_days) * 480)
    return 2 * 480


def build_estimates(request: EstimateRequest) -> EstimateResponse:
    estimates: list[EstimateItem] = []

    for task in request.task_inputs:
        likely_minutes = _base_minutes_from_task_name(task.task_name, task.duration)
        optimistic_minutes = max(120, int(likely_minutes * 0.7))
        pessimistic_minutes = max(optimistic_minutes + 60, int(likely_minutes * 1.6))
        confidence = 0.78 if task.duration else 0.64
        reasoning = (
            f"Estimated from task context and comparable PM work patterns for '{task.task_name}'."
            if request.include_reasoning
            else None
        )

        estimates.append(
            EstimateItem(
                task_id=task.task_id,
                task_name=task.task_name,
                optimistic_minutes=optimistic_minutes,
                likely_minutes=likely_minutes,
                pessimistic_minutes=pessimistic_minutes,
                recommended_minutes=likely_minutes,
                confidence=confidence,
                reasoning=reasoning,
            )
        )

    usage = AIUsageMeta(
        tokens_in=estimate_tokens(
            request.project_context.name + " ".join(task.task_name for task in request.task_inputs)
        ),
        tokens_out=estimate_tokens(str(len(estimates))),
        model=settings.AI_MODEL_NAME,
    )
    return EstimateResponse(estimates=estimates, usage=usage)


def build_suggestions(request: SuggestionsRequest) -> SuggestionsResponse:
    suggestions: list[SuggestionItem] = []
    today = date.today()

    for task in request.project_context.tasks:
        if len(suggestions) >= request.limit:
            break
        if task.percent_complete < 100 and task.finish_date < today:
            suggestions.append(
                SuggestionItem(
                    id=f"s-{uuid4()}",
                    type="OVERDUE_TASK",
                    severity="HIGH",
                    title="Task is overdue",
                    description=f"'{task.name}' is past finish date and still incomplete.",
                    affected_task_id=task.id,
                    suggested_action=SuggestionAction(
                        type="SET_PRIORITY",
                        payload={"task_id": str(task.id), "priority": 850},
                    ),
                )
            )

    lower_names = [task.name.lower() for task in request.project_context.tasks]
    has_qa = any("qa" in name or "test" in name for name in lower_names)
    has_deploy = any("deploy" in name or "release" in name for name in lower_names)
    if len(suggestions) < request.limit and has_qa and has_deploy:
        qa_task = next(
            (
                t
                for t in request.project_context.tasks
                if "qa" in t.name.lower() or "test" in t.name.lower()
            ),
            None,
        )
        deploy_task = next(
            (
                t
                for t in request.project_context.tasks
                if "deploy" in t.name.lower() or "release" in t.name.lower()
            ),
            None,
        )
        if qa_task and deploy_task:
            suggestions.append(
                SuggestionItem(
                    id=f"s-{uuid4()}",
                    type="MISSING_DEPENDENCY",
                    severity="MEDIUM",
                    title="Possible missing dependency",
                    description=(
                        f"'{deploy_task.name}' likely depends on '{qa_task.name}'. "
                        "Add dependency to enforce sequence."
                    ),
                    affected_task_id=deploy_task.id,
                    suggested_action=SuggestionAction(
                        type="ADD_DEPENDENCY",
                        payload={
                            "predecessor_id": str(qa_task.id),
                            "successor_id": str(deploy_task.id),
                            "dependency_type": "FS",
                        },
                    ),
                )
            )

    if not suggestions:
        suggestions.append(
            SuggestionItem(
                id=f"s-{uuid4()}",
                type="NO_CRITICAL_ISSUE",
                severity="LOW",
                title="No high-risk issues detected",
                description="Current schedule looks stable based on available task signals.",
                suggested_action=SuggestionAction(type="NONE", payload={}),
            )
        )

    usage = AIUsageMeta(
        tokens_in=estimate_tokens(request.project_context.name + str(len(request.project_context.tasks))),
        tokens_out=estimate_tokens(str(len(suggestions))),
        model=settings.AI_MODEL_NAME,
    )
    return SuggestionsResponse(suggestions=suggestions[: request.limit], usage=usage)
