from typing import Any, cast

from openai.types.chat import ChatCompletionToolUnionParam


def as_openai_tools(tool_definitions: list[dict[str, Any]]) -> list[ChatCompletionToolUnionParam]:
    tools: list[ChatCompletionToolUnionParam] = []
    for tool in tool_definitions:
        tools.append(
            cast(
                ChatCompletionToolUnionParam,
                {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
                },
                },
            ),
        )
    return tools


def as_gemini_tools(tool_definitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    for tool in tool_definitions:
        declarations.append(
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
            }
        )
    return [{"functionDeclarations": declarations}]
