import logging
from typing import Any
from uuid import uuid4

import httpx

from app.core.config import settings
from app.schema.contracts import AIUsageMeta, ChatEvent, ChatRequest
from app.service.providers.common import build_system_prompt
from app.service.providers.message_builders import build_gemini_contents
from app.service.providers.tool_adapters import as_gemini_tools

logger = logging.getLogger(__name__)


async def stream_gemini(
    request: ChatRequest,
    *,
    model_id: str,
    tool_definitions: list[dict[str, Any]],
):
    system = build_system_prompt(request)
    contents = build_gemini_contents(request)
    tools = as_gemini_tools(tool_definitions)

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "tools": tools,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                params={"key": settings.GEMINI_API_KEY},
                json=payload,
            )
    except Exception:
        logger.exception("Gemini chat request failed")
        yield ChatEvent(type="error", error="Gemini API call failed").model_dump(
            mode="json", exclude_none=True
        )
        return

    if response.status_code >= 400:
        logger.error("Gemini API error status=%s body=%s", response.status_code, response.text)
        yield ChatEvent(type="error", error="Gemini API call failed").model_dump(
            mode="json", exclude_none=True
        )
        return

    try:
        data = response.json()
    except ValueError:
        yield ChatEvent(type="error", error="Malformed Gemini response").model_dump(
            mode="json", exclude_none=True
        )
        return

    candidate = (data.get("candidates") or [{}])[0]
    parts = ((candidate.get("content") or {}).get("parts")) or []

    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            yield ChatEvent(type="chunk", content=part["text"]).model_dump(
                mode="json", exclude_none=True
            )
        function_call = part.get("functionCall") if isinstance(part, dict) else None
        if function_call:
            yield ChatEvent(
                type="tool_call",
                tool_use_id=str(uuid4()),
                tool_name=function_call.get("name"),
                tool_input=function_call.get("args") or {},
            ).model_dump(mode="json", exclude_none=True)

    usage_meta = data.get("usageMetadata") or {}
    usage = AIUsageMeta(
        tokens_in=int(usage_meta.get("promptTokenCount", 0) or 0),
        tokens_out=int(usage_meta.get("candidatesTokenCount", 0) or 0),
        model=model_id,
    )
    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)
