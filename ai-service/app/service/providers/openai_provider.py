import json
import logging
from typing import Any, cast
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

    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[system_message, *messages],
            tools=tools,
            tool_choice="auto",
        )
    except Exception:
        logger.exception("OpenAI chat request failed")
        yield ChatEvent(type="error", error="OpenAI API call failed").model_dump(
            mode="json", exclude_none=True
        )
        return

    choice = response.choices[0] if response.choices else None
    message = choice.message if choice else None

    if message and message.content:
        yield ChatEvent(type="chunk", content=message.content).model_dump(
            mode="json", exclude_none=True
        )

    if message and message.tool_calls:
        for call in message.tool_calls:
            # OpenAI can return non-function custom tool calls; only function calls
            # map to our current tool_call SSE contract.
            if getattr(call, "type", None) != "function":
                continue
            function_call = cast(Any, call).function
            raw_args = function_call.arguments or "{}"
            try:
                parsed_input = json.loads(raw_args)
            except json.JSONDecodeError:
                parsed_input = {}
            yield ChatEvent(
                type="tool_call",
                tool_use_id=call.id,
                tool_name=function_call.name,
                tool_input=parsed_input,
            ).model_dump(mode="json", exclude_none=True)

    usage = AIUsageMeta(
        tokens_in=response.usage.prompt_tokens if response.usage else 0,
        tokens_out=response.usage.completion_tokens if response.usage else 0,
        model=model_id,
    )
    yield ChatEvent(
        type="done",
        message_id=uuid4(),
        usage=usage,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)
