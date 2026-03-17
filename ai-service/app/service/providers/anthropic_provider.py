import json
import logging
from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.schema.contracts import AIUsageMeta, ChatEvent

logger = logging.getLogger(__name__)


async def stream_claude(
    messages: list[dict],
    system_prompt: str,
    tools: list[dict],
    *,
    model_id: str,
    api_key: str | None = None,
    conversation_id: UUID | None = None,
):
    from anthropic import AsyncAnthropic

    effective_key = api_key or settings.ANTHROPIC_API_KEY
    client = AsyncAnthropic(api_key=effective_key)

    yield ChatEvent(
        type="start",
        conversation_id=conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    current_tool_id: str | None = None
    current_tool_name: str | None = None
    tool_input_json = ""
    final_message = None

    stream_kwargs: dict[str, Any] = {
        "model": model_id,
        "max_tokens": 8096,
        "system": system_prompt,
        "messages": messages,
    }
    if tools:
        stream_kwargs["tools"] = tools

    try:
        async with client.messages.stream(**stream_kwargs) as stream:
            async for event in stream:
                event_type = getattr(event, "type", None)

                if event_type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool_id = block.id
                        current_tool_name = block.name
                        tool_input_json = ""

                elif event_type == "content_block_delta":
                    delta = event.delta
                    if getattr(delta, "type", None) == "text_delta":
                        yield ChatEvent(type="chunk", content=delta.text).model_dump(
                            mode="json", exclude_none=True
                        )
                    elif getattr(delta, "type", None) == "input_json_delta":
                        tool_input_json += delta.partial_json

                elif event_type == "content_block_stop":
                    if current_tool_id is not None:
                        if not current_tool_name:
                            logger.warning("Anthropic returned a tool call with no name — skipping")
                            current_tool_id = None
                            current_tool_name = None
                            tool_input_json = ""
                            continue
                        try:
                            tool_input = json.loads(tool_input_json) if tool_input_json else {}
                        except json.JSONDecodeError:
                            tool_input = {}

                        yield ChatEvent(
                            type="tool_call",
                            tool_use_id=current_tool_id,
                            tool_name=current_tool_name,
                            tool_input=tool_input,
                        ).model_dump(mode="json", exclude_none=True)

                        current_tool_id = None
                        current_tool_name = None
                        tool_input_json = ""

            final_message = await stream.get_final_message()

    except Exception:
        logger.exception("Claude streaming failed")
        yield ChatEvent(type="error", error="Claude API call failed").model_dump(
            mode="json", exclude_none=True
        )
        return

    usage = AIUsageMeta(
        tokens_in=final_message.usage.input_tokens if final_message else 0,
        tokens_out=final_message.usage.output_tokens if final_message else 0,
        model=model_id,
    )
    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)
