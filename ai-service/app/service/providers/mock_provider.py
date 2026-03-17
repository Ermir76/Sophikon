import asyncio
from uuid import UUID, uuid4

from app.schema.contracts import AIUsageMeta, ChatEvent
from app.service.providers.common import chunk_text, estimate_tokens


def _compose_mock_answer(messages: list[dict]) -> str:
    last_user = next(
        (m for m in reversed(messages) if m.get("role") == "user"), None
    )
    if last_user is None:
        return "No user message received."
    content = last_user.get("content", "")
    if isinstance(content, list):
        text = " ".join(
            b.get("text", b.get("content", ""))
            for b in content
            if isinstance(b, dict)
        )
    else:
        text = str(content)

    question = text.lower()
    if "overdue" in question:
        return "I checked the project. Several tasks appear overdue. I recommend prioritising tasks past their finish date."
    if "progress" in question or "status" in question:
        return "The project is currently in progress. Some tasks are complete, some are still active."
    if "suggest" in question or "next" in question:
        return "Recommended: resolve overdue tasks first, then focus on in-progress items to improve schedule confidence."
    return f"I reviewed your request: '{text[:100]}'. Let me know how you'd like to proceed."


async def stream_mock(
    messages: list[dict],
    system_prompt: str,
    *,
    model_id: str,
    conversation_id: UUID | None = None,
):
    answer = _compose_mock_answer(messages)
    usage = AIUsageMeta(
        tokens_in=estimate_tokens(system_prompt),
        tokens_out=estimate_tokens(answer),
        model=model_id,
    )

    yield ChatEvent(
        type="start",
        conversation_id=conversation_id,
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
