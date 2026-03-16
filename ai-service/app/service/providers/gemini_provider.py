import asyncio
import json
import logging
from typing import Any
from uuid import uuid4

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
    import google.generativeai as genai

    system = build_system_prompt(request)
    contents = build_gemini_contents(request)
    tools = as_gemini_tools(tool_definitions)

    yield ChatEvent(
        type="start",
        conversation_id=request.conversation_id,
        model=model_id,
    ).model_dump(mode="json", exclude_none=True)

    def _part_value(part: object, attr: str, alt: str) -> object | None:
        if isinstance(part, dict):
            return part.get(attr) or part.get(alt)
        return getattr(part, attr, None) or getattr(part, alt, None)

    def _extract_usage_counts(chunk: object) -> tuple[int, int]:
        usage_meta = getattr(chunk, "usage_metadata", None) or getattr(chunk, "usageMetadata", None)
        if isinstance(usage_meta, dict):
            prompt = int(
                usage_meta.get("prompt_token_count")
                or usage_meta.get("promptTokenCount")
                or 0
            )
            completion = int(
                usage_meta.get("candidates_token_count")
                or usage_meta.get("candidatesTokenCount")
                or 0
            )
            return prompt, completion
        if usage_meta is None:
            return 0, 0
        prompt = int(
            getattr(usage_meta, "prompt_token_count", None)
            or getattr(usage_meta, "promptTokenCount", None)
            or 0
        )
        completion = int(
            getattr(usage_meta, "candidates_token_count", None)
            or getattr(usage_meta, "candidatesTokenCount", None)
            or 0
        )
        return prompt, completion

    def _normalize_function_args(raw_args: object) -> dict[str, Any]:
        if isinstance(raw_args, dict):
            return raw_args
        if raw_args is None:
            return {}
        if hasattr(raw_args, "items"):
            return {str(k): v for k, v in raw_args.items()}
        if isinstance(raw_args, str):
            try:
                parsed = json.loads(raw_args)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {}
        return {}

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=model_id,
        system_instruction=system,
        tools=tools,
    )

    prompt_tokens = 0
    completion_tokens = 0

    queue: asyncio.Queue[tuple[str, object | None]] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _produce_stream() -> None:
        try:
            response_stream = model.generate_content(contents, stream=True)
            for chunk in response_stream:
                loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

    producer = asyncio.create_task(asyncio.to_thread(_produce_stream))

    try:
        while True:
            item_type, payload = await queue.get()
            if item_type == "done":
                break
            if item_type == "error":
                raise payload if isinstance(payload, Exception) else RuntimeError(
                    "Gemini stream failed"
                )

            chunk = payload
            text = getattr(chunk, "text", None)
            if isinstance(text, str) and text:
                yield ChatEvent(type="chunk", content=text).model_dump(
                    mode="json", exclude_none=True
                )

            candidates = getattr(chunk, "candidates", None) or []
            for candidate in candidates:
                content = _part_value(candidate, "content", "content")
                parts = _part_value(content, "parts", "parts") or []
                for part in parts:
                    function_call = _part_value(part, "function_call", "functionCall")
                    if not function_call:
                        continue
                    tool_name = _part_value(function_call, "name", "name")
                    tool_args_raw = _part_value(function_call, "args", "args")
                    yield ChatEvent(
                        type="tool_call",
                        tool_use_id=str(uuid4()),
                        tool_name=str(tool_name) if tool_name else None,
                        tool_input=_normalize_function_args(tool_args_raw),
                    ).model_dump(mode="json", exclude_none=True)

            p_tokens, c_tokens = _extract_usage_counts(chunk)
            if p_tokens:
                prompt_tokens = p_tokens
            if c_tokens:
                completion_tokens = c_tokens
    except Exception:
        logger.exception("Gemini chat request failed")
        yield ChatEvent(type="error", error="Gemini API call failed").model_dump(
            mode="json", exclude_none=True
        )
        return
    finally:
        await producer

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
