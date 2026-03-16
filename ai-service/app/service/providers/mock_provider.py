import asyncio
from datetime import date
from uuid import uuid4

from app.schema.contracts import AIUsageMeta, ChatEvent, ChatRequest
from app.service.providers.common import chunk_text, estimate_tokens


def compose_mock_answer(request: ChatRequest) -> str:
    tasks = request.project_context.tasks
    today = date.today()
    overdue = sum(1 for t in tasks if t.percent_complete < 100 and t.finish_date < today)
    in_progress = sum(1 for t in tasks if 0 < t.percent_complete < 100)
    completed = sum(1 for t in tasks if t.percent_complete >= 100)
    total = len(tasks)
    name = request.project_context.name
    question = (request.message or "").lower()

    if "overdue" in question:
        return (
            f"{name} has {overdue} overdue tasks out of {total}. "
            "Prioritize tasks with past finish dates and low completion."
        )
    if "progress" in question or "status" in question:
        return (
            f"{name}: {completed} completed, {in_progress} in progress, {overdue} overdue "
            f"out of {total} total tasks."
        )
    if "suggest" in question or "next" in question:
        return (
            f"Recommended: resolve {overdue} overdue tasks first, then focus on "
            f"{in_progress} active tasks to improve schedule confidence."
        )
    return (
        f"I reviewed {name}: {completed}/{total} tasks complete, "
        f"{in_progress} in progress, {overdue} overdue. "
        "Ask about overdue tasks, progress, or schedule suggestions."
    )


async def stream_mock(request: ChatRequest, *, model_id: str):
    answer = compose_mock_answer(request)
    usage = AIUsageMeta(
        tokens_in=estimate_tokens(request.message or ""),
        tokens_out=estimate_tokens(answer),
        model=model_id,
    )

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    for chunk in chunk_text(answer):
        await asyncio.sleep(0)
        yield ChatEvent(type="chunk", content=chunk).model_dump(mode="json", exclude_none=True)

    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)
