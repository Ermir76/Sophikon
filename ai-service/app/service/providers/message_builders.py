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
        content = stringify_content(item.content)
        if role == "assistant":
            assistant_message: ChatCompletionAssistantMessageParam = {
                "role": "assistant",
                "content": content,
            }
            messages.append(assistant_message)
        elif role == "system":
            system_message: ChatCompletionSystemMessageParam = cast(
                ChatCompletionSystemMessageParam,
                {"role": "system", "content": content},
            )
            messages.append(system_message)
        else:
            user_message: ChatCompletionUserMessageParam = cast(
                ChatCompletionUserMessageParam,
                {"role": "user", "content": content},
            )
            messages.append(user_message)

    if request.tool_results:
        tool_results_payload = [
            {
                "tool_use_id": tr.tool_use_id,
                "content": tr.content,
                **({"is_error": True} if tr.is_error else {}),
            }
            for tr in request.tool_results
        ]
        tool_results_message: ChatCompletionUserMessageParam = cast(
            ChatCompletionUserMessageParam,
            {
                "role": "user",
                "content": f"Tool results: {json.dumps(tool_results_payload, ensure_ascii=False)}",
            },
        )
        messages.append(tool_results_message)
    elif request.message:
        user_prompt_message: ChatCompletionUserMessageParam = cast(
            ChatCompletionUserMessageParam,
            {"role": "user", "content": request.message},
        )
        messages.append(user_prompt_message)

    return messages


def build_gemini_contents(request: ChatRequest) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for item in request.history:
        role = "model" if item.role == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": stringify_content(item.content)}]})

    if request.tool_results:
        tool_results_payload = [
            {
                "tool_use_id": tr.tool_use_id,
                "content": tr.content,
                **({"is_error": True} if tr.is_error else {}),
            }
            for tr in request.tool_results
        ]
        contents.append(
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"Tool results: {json.dumps(tool_results_payload, ensure_ascii=False)}"
                    }
                ],
            }
        )
    elif request.message:
        contents.append({"role": "user", "parts": [{"text": request.message}]})

    return contents
