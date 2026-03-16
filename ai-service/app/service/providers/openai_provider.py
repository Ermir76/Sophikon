import json
import logging
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.schema.contracts import AIUsageMeta, ChatEvent, ChatRequest
from app.service.providers.common import build_system_prompt
from app.service.providers.message_builders import build_openai_messages
from app.service.providers.tool_adapters import as_openai_tools
from openai.types.chat import ChatCompletionSystemMessageParam

logger = logging.getLogger(__name__)


async def stream_openai(
    request: ChatRequest,
    *,
    model_id: str,
    tool_definitions: list[dict[str, Any]],
):
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    messages = build_openai_messages(request)
    system = build_system_prompt(request)
    tools = as_openai_tools(tool_definitions)
    system_message: ChatCompletionSystemMessageParam = {"role": "system", "content": system}

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    def _delta_text(value: object) -> str | None:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts: list[str] = []
            for item in value:
                if isinstance(item, dict):
                    maybe_text = item.get("text")
                    if isinstance(maybe_text, str):
                        parts.append(maybe_text)
            return "".join(parts) if parts else None
        return None

    pending_tool_calls: dict[int, dict[str, str]] = {}
    prompt_tokens = 0
    completion_tokens = 0

    try:
        stream = await client.chat.completions.create(
            model=model_id,
            messages=[system_message, *messages],
            tools=tools,
            tool_choice="auto",
            stream=True,
            stream_options={"include_usage": True},
        )

        async for chunk in stream:
            if getattr(chunk, "usage", None):
                prompt_tokens = int(getattr(chunk.usage, "prompt_tokens", 0) or 0)
                completion_tokens = int(getattr(chunk.usage, "completion_tokens", 0) or 0)

            for choice in getattr(chunk, "choices", []) or []:
                delta = getattr(choice, "delta", None)
                if delta is None:
                    continue

                text = _delta_text(getattr(delta, "content", None))
                if text:
                    yield ChatEvent(type="chunk", content=text).model_dump(
                        mode="json", exclude_none=True
                    )

                for call in getattr(delta, "tool_calls", None) or []:
                    if getattr(call, "type", None) != "function":
                        continue
                    index = int(getattr(call, "index", 0) or 0)
                    current = pending_tool_calls.setdefault(
                        index,
                        {"id": str(uuid4()), "name": "", "arguments": ""},
                    )
                    if getattr(call, "id", None):
                        current["id"] = str(call.id)

                    function = getattr(call, "function", None)
                    if function is None:
                        continue
                    if getattr(function, "name", None):
                        current["name"] = str(function.name)
                    if getattr(function, "arguments", None):
                        current["arguments"] += str(function.arguments)
    except Exception:
        logger.exception("OpenAI chat request failed")
        yield ChatEvent(type="error", error="OpenAI API call failed").model_dump(
            mode="json", exclude_none=True
        )
        return

    for index in sorted(pending_tool_calls):
        pending = pending_tool_calls[index]
        raw_args = pending["arguments"] or "{}"
        try:
            parsed_input = json.loads(raw_args)
        except json.JSONDecodeError:
            parsed_input = {}
        yield ChatEvent(
            type="tool_call",
            tool_use_id=pending["id"],
            tool_name=pending["name"] or None,
            tool_input=parsed_input if isinstance(parsed_input, dict) else {},
        ).model_dump(mode="json", exclude_none=True)

    usage = AIUsageMeta(
        tokens_in=prompt_tokens,
        tokens_out=completion_tokens,
        model=model_id,
    )
    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)
