"""
Convert messages from the standard anthropic-format list[dict] to each
provider's native wire format.

Standard format (backend sends this):
  user text:     {"role": "user",      "content": "string"}
  user tools:    {"role": "user",      "content": [{"type": "tool_result", ...}]}
  assistant text:{"role": "assistant", "content": "string"}
  assistant+tools:{"role":"assistant", "content": [{"type":"text",...},{"type":"tool_use",...}]}
"""

import json
from typing import Any, cast

from app.service.providers.common import stringify_content
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)


def to_openai_messages(messages: list[dict]) -> list[ChatCompletionMessageParam]:
    """Convert anthropic-format messages to OpenAI chat completion format."""
    result: list[ChatCompletionMessageParam] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if isinstance(content, list):
            if role == "assistant":
                tool_calls = []
                text_parts = []
                for block in content:
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
                result.append(
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
                # user role with tool_result blocks
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        result.append(
                            cast(
                                ChatCompletionMessageParam,
                                {
                                    "role": "tool",
                                    "tool_call_id": block.get("tool_use_id", ""),
                                    "content": block.get("content", ""),
                                },
                            )
                        )
        else:
            text = stringify_content(content)
            if role == "assistant":
                result.append(
                    cast(
                        ChatCompletionAssistantMessageParam,
                        {"role": "assistant", "content": text},
                    )
                )
            else:
                result.append(
                    cast(
                        ChatCompletionUserMessageParam,
                        {"role": "user", "content": text},
                    )
                )

    return result


def to_gemini_contents(messages: list[dict]) -> list[dict[str, Any]]:
    """Convert anthropic-format messages to Gemini contents format."""
    contents: list[dict[str, Any]] = []

    # Build tool_use_id -> name map (Gemini needs the function name in functionResponse)
    tool_name_map: dict[str, str] = {}
    for msg in messages:
        if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
            for block in msg["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_name_map[block["id"]] = block["name"]

    for msg in messages:
        role = "model" if msg.get("role") == "assistant" else "user"
        content = msg.get("content", "")

        if isinstance(content, list):
            parts: list[dict[str, Any]] = []
            if msg.get("role") == "assistant":
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        parts.append(
                            {
                                "function_call": {
                                    "name": block["name"],
                                    "args": block.get("input", {}),
                                }
                            }
                        )
                    elif isinstance(block, dict) and block.get("type") == "text":
                        parts.append({"text": block.get("text", "")})
            else:
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_id = block.get("tool_use_id", "")
                        tool_name = tool_name_map.get(tool_id, tool_id)
                        raw = block.get("content", "")
                        try:
                            parsed = json.loads(raw) if raw else {}
                            response_data = parsed if isinstance(parsed, dict) else {"result": raw}
                        except (json.JSONDecodeError, TypeError):
                            response_data = {"result": raw}
                        parts.append(
                            {
                                "function_response": {
                                    "name": tool_name,
                                    "response": response_data,
                                }
                            }
                        )
            if parts:
                contents.append({"role": role, "parts": parts})
        else:
            contents.append(
                {"role": role, "parts": [{"text": stringify_content(content)}]}
            )

    return contents
