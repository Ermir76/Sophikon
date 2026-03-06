import asyncio
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


def _estimate_tokens(value: str) -> int:
    return max(1, len(value) // 4)


def _chunk_text(value: str, chunk_size: int = 48) -> list[str]:
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]


def _summarize_status(request: ChatRequest) -> tuple[int, int, int]:
    tasks = request.project_context.tasks
    overdue = 0
    in_progress = 0
    completed = 0
    today = date.today()

    for task in tasks:
        if task.percent_complete >= 100:
            completed += 1
            continue
        if task.percent_complete > 0:
            in_progress += 1
        if task.finish_date < today:
            overdue += 1

    return overdue, in_progress, completed


def _compose_chat_answer(request: ChatRequest) -> str:
    overdue, in_progress, completed = _summarize_status(request)
    total = len(request.project_context.tasks)
    question = request.message.lower()
    project_name = request.project_context.name

    if "overdue" in question:
        return (
            f"{project_name} has {overdue} overdue tasks out of {total}. "
            "Prioritize tasks with past finish dates and low completion."
        )

    if "progress" in question or "status" in question:
        return (
            f"{project_name} currently has {completed} completed tasks, "
            f"{in_progress} in progress, and {overdue} overdue."
        )

    if "suggest" in question or "next" in question:
        return (
            f"Recommended next step: resolve {overdue} overdue tasks first, then focus "
            f"on the {in_progress} active tasks to improve schedule confidence."
        )

    return (
        f"I reviewed {project_name}: {completed}/{total} tasks are complete, "
        f"{in_progress} are in progress, and {overdue} are overdue. "
        "Ask for overdue details, progress, or schedule suggestions."
    )


async def stream_chat_events(request: ChatRequest):
    answer = _compose_chat_answer(request)
    conversation_id = request.conversation_id
    usage = AIUsageMeta(
        tokens_in=_estimate_tokens(request.message),
        tokens_out=_estimate_tokens(answer),
        model=settings.AI_MODEL_NAME,
    )

    yield ChatEvent(
        type="start",
        conversation_id=conversation_id,
        model=settings.AI_MODEL_NAME,
    ).model_dump(mode="json", exclude_none=True)

    for chunk in _chunk_text(answer):
        await asyncio.sleep(0)
        yield ChatEvent(type="chunk", content=chunk).model_dump(
            mode="json", exclude_none=True
        )

    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=settings.AI_MODEL_NAME,
    ).model_dump(mode="json", exclude_none=True)


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
        tokens_in=_estimate_tokens(
            request.project_context.name + " ".join(task.task_name for task in request.task_inputs)
        ),
        tokens_out=_estimate_tokens(str(len(estimates))),
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
                task
                for task in request.project_context.tasks
                if "qa" in task.name.lower() or "test" in task.name.lower()
            ),
            None,
        )
        deploy_task = next(
            (
                task
                for task in request.project_context.tasks
                if "deploy" in task.name.lower() or "release" in task.name.lower()
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
        tokens_in=_estimate_tokens(request.project_context.name + str(len(request.project_context.tasks))),
        tokens_out=_estimate_tokens(str(len(suggestions))),
        model=settings.AI_MODEL_NAME,
    )
    return SuggestionsResponse(suggestions=suggestions[: request.limit], usage=usage)
