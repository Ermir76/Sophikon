import json
from typing import Any, cast

from app.schema.contracts import ChatRequest
from app.service.providers.common import stringify_content
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)


def build_claude_messages(request: ChatRequest) -> list[dict]:
    messages: list[dict] = []

    for item in request.history:
        messages.append({"role": item.role, "content": item.content})

    if request.tool_results:
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tr.tool_use_id,
                        "content": tr.content,
                        **({"is_error": True} if tr.is_error else {}),
                    }
                    for tr in request.tool_results
                ],
            }
        )
    elif request.message:
        messages.append({"role": "user", "content": request.message})

    return messages


def build_openai_messages(request: ChatRequest) -> list[ChatCompletionMessageParam]:
    messages: list[ChatCompletionMessageParam] = []
    for item in request.history:
        role = item.role if item.role in {"user", "assistant", "system"} else "user"

        if isinstance(item.content, list):
            if role == "assistant":
                tool_calls = []
                text_parts = []
                for block in item.content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_calls.append(
                            {
                                "id": block["id"],
                                "type": "function",
                                "function": {
                                    "name": block["name"],
                                    "arguments": json.dumps(block.get("input", {})),
                                },
                            }
                        )
                    elif isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                messages.append(
                    cast(
                        ChatCompletionAssistantMessageParam,
                        {
                            "role": "assistant",
                            "content": " ".join(text_parts) or None,
                            "tool_calls": tool_calls,
                        },
                    )
                )
            else:
                for block in item.content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        messages.append(
                            cast(
                                ChatCompletionMessageParam,
                                {
                                    "role": "tool",
                                    "tool_call_id": block["tool_use_id"],
                                    "content": block.get("content", ""),
                                },
                            )
                        )
        else:
            content = stringify_content(item.content)
            if role == "assistant":
                messages.append(
                    cast(
                        ChatCompletionAssistantMessageParam,
                        {"role": "assistant", "content": content},
                    )
                )
            elif role == "system":
                messages.append(
                    cast(
                        ChatCompletionSystemMessageParam,
                        {"role": "system", "content": content},
                    )
                )
            else:
                messages.append(
                    cast(
                        ChatCompletionUserMessageParam,
                        {"role": "user", "content": content},
                    )
                )

    if request.tool_results:
        for tr in request.tool_results:
            messages.append(
                cast(
                    ChatCompletionMessageParam,
                    {
                        "role": "tool",
                        "tool_call_id": tr.tool_use_id,
                        "content": tr.content,
                    },
                )
            )
    elif request.message:
        messages.append(
            cast(
                ChatCompletionUserMessageParam,
                {"role": "user", "content": request.message},
            )
        )

    return messages


def _parse_gemini_response(content: str) -> dict:
    try:
        parsed = json.loads(content) if content else {}
        return parsed if isinstance(parsed, dict) else {"result": content}
    except (json.JSONDecodeError, TypeError):
        return {"result": content}


def build_gemini_contents(request: ChatRequest) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []

    # Build tool_use_id -> name map (needed for functionResponse which requires the name)
    tool_name_map: dict[str, str] = {}
    for item in request.history:
        if item.role == "assistant" and isinstance(item.content, list):
            for block in item.content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_name_map[block["id"]] = block["name"]

    for item in request.history:
        role = "model" if item.role == "assistant" else "user"

        if isinstance(item.content, list):
            parts: list[dict[str, Any]] = []
            if item.role == "assistant":
                for block in item.content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        parts.append(
                            {"function_call": {"name": block["name"], "args": block.get("input", {})}}
                        )
                    elif isinstance(block, dict) and block.get("type") == "text":
                        parts.append({"text": block.get("text", "")})
            else:
                for block in item.content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_id = block.get("tool_use_id", "")
                        tool_name = tool_name_map.get(tool_id, tool_id)
                        parts.append(
                            {
                                "function_response": {
                                    "name": tool_name,
                                    "response": _parse_gemini_response(block.get("content", "")),
                                }
                            }
                        )
            if parts:
                contents.append({"role": role, "parts": parts})
        else:
            contents.append({"role": role, "parts": [{"text": stringify_content(item.content)}]})

    if request.tool_results:
        parts = [
            {
                "function_response": {
                    "name": tool_name_map.get(tr.tool_use_id, tr.tool_use_id),
                    "response": _parse_gemini_response(tr.content),
                }
            }
            for tr in request.tool_results
        ]
        contents.append({"role": "user", "parts": parts})
    elif request.message:
        contents.append({"role": "user", "parts": [{"text": request.message}]})

    return contents
