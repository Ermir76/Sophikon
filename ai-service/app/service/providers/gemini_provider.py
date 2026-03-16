import logging
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.schema.contracts import AIUsageMeta, ChatEvent, ChatRequest
from app.service.providers.common import build_system_prompt
from app.service.providers.message_builders import build_gemini_contents

logger = logging.getLogger(__name__)


async def stream_gemini(
    request: ChatRequest,
    *,
    model_id: str,
    tool_definitions: list[dict[str, Any]],
):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    system = build_system_prompt(request)
    contents = build_gemini_contents(request)

    declarations = [
        types.FunctionDeclaration(
            name=tool["name"],
            description=tool.get("description", ""),
            parameters=tool.get("input_schema", {"type": "object", "properties": {}}),
        )
        for tool in tool_definitions
    ]
    tools = [types.Tool(function_declarations=declarations)] if declarations else []

    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=tools,
    )

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    prompt_tokens = 0
    completion_tokens = 0
    pending_tool_calls: list[dict[str, Any]] = []

    try:
        response_stream = await client.aio.models.generate_content_stream(
            model=model_id,
            contents=contents,
            config=config,
        )
        async for chunk in response_stream:
            usage_meta = getattr(chunk, "usage_metadata", None)
            if usage_meta:
                p = getattr(usage_meta, "prompt_token_count", None)
                c = getattr(usage_meta, "candidates_token_count", None)
                if p:
                    prompt_tokens = int(p)
                if c:
                    completion_tokens = int(c)

            text = getattr(chunk, "text", None)
            if isinstance(text, str) and text:
                yield ChatEvent(type="chunk", content=text).model_dump(
                    mode="json", exclude_none=True
                )

            for candidate in getattr(chunk, "candidates", None) or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", None) or []:
                    fc = getattr(part, "function_call", None)
                    if not fc:
                        continue
                    name = getattr(fc, "name", None)
                    args_raw = getattr(fc, "args", None)
                    args: dict[str, Any] = {}
                    if isinstance(args_raw, dict):
                        args = args_raw
                    elif args_raw is not None and hasattr(args_raw, "items"):
                        args = {str(k): v for k, v in args_raw.items()}
                    pending_tool_calls.append(
                        {"id": str(uuid4()), "name": str(name) if name else "", "args": args}
                    )

    except Exception:
        logger.exception("Gemini chat request failed")
        yield ChatEvent(type="error", error="Gemini API call failed").model_dump(
            mode="json", exclude_none=True
        )
        return

    for tc in pending_tool_calls:
        yield ChatEvent(
            type="tool_call",
            tool_use_id=tc["id"],
            tool_name=tc["name"] or None,
            tool_input=tc["args"],
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
