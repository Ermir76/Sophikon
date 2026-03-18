import asyncio
from uuid import UUID, uuid4

from app.schema.contracts import AIUsageMeta, ChatEvent
from app.service.providers.common import chunk_text, estimate_tokens


def _compose_mock_answer(messages: list[dict], system_prompt: str = "") -> str:
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

    if "Return ONLY valid JSON" in system_prompt:
        return _compose_mock_json_answer(system_prompt, text)

    question = text.lower()
    if "overdue" in question:
        return "I checked the project. Several tasks appear overdue. I recommend prioritising tasks past their finish date."
    if "progress" in question or "status" in question:
        return "The project is currently in progress. Some tasks are complete, some are still active."
    if "suggest" in question or "next" in question:
        return "Recommended: resolve overdue tasks first, then focus on in-progress items to improve schedule confidence."
    return f"I reviewed your request: '{text[:100]}'. Let me know how you'd like to proceed."


def _compose_mock_json_answer(system_prompt: str, user_text: str) -> str:
    import json
    import re

    if "optimistic_minutes" in system_prompt:
        task_ids = re.findall(r"id:([a-f0-9-]{36})", user_text)
        task_names = re.findall(r"- (.+?) \(id:", user_text)
        estimates = [
            {
                "task_id": task_ids[i] if i < len(task_ids) else None,
                "task_name": task_names[i] if i < len(task_names) else f"Task {i + 1}",
                "optimistic_minutes": 240,
                "likely_minutes": 480,
                "pessimistic_minutes": 960,
                "recommended_minutes": 480,
                "confidence": 0.75,
                "reasoning": "Mock estimate based on task complexity.",
            }
            for i in range(max(len(task_ids), 1))
        ]
        return json.dumps({"estimates": estimates})

    if "suggested_action" in system_prompt:
        return json.dumps(
            {
                "suggestions": [
                    {
                        "id": "mock-sug-1",
                        "type": "SCHEDULE_RISK",
                        "severity": "MEDIUM",
                        "title": "Review overdue tasks",
                        "description": "Some tasks appear to be behind schedule.",
                        "affected_task_id": None,
                        "suggested_action": {"type": "NONE", "payload": {}},
                    }
                ]
            }
        )

    return json.dumps({"result": "mock response"})


async def stream_mock(
    messages: list[dict],
    system_prompt: str,
    *,
    model_id: str,
    conversation_id: UUID | None = None,
):
    answer = _compose_mock_answer(messages, system_prompt)
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
