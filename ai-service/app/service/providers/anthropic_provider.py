import json
import logging
from uuid import uuid4

from app.core.config import settings
from app.schema.contracts import AIUsageMeta, ChatEvent, ChatRequest
from app.service.providers.common import build_system_prompt
from app.service.providers.message_builders import build_claude_messages

logger = logging.getLogger(__name__)


async def stream_claude(
    request: ChatRequest,
    *,
    model_id: str,
    tool_definitions: list[dict],
):
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    messages = build_claude_messages(request)
    system = build_system_prompt(request)

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    current_tool_id: str | None = None
    current_tool_name: str | None = None
    tool_input_json = ""
    final_message = None

    try:
        async with client.messages.stream(
            model=model_id,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=tool_definitions,
        ) as stream:
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
