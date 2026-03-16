from app.service.providers.tool_adapters import as_gemini_tools, as_openai_tools
from app.service.providers.tool_catalog import TOOL_DEFINITIONS


def test_as_openai_tools_maps_function_shape():
    tools = as_openai_tools(TOOL_DEFINITIONS[:1])
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == TOOL_DEFINITIONS[0]["name"]


def test_as_gemini_tools_maps_function_declarations_shape():
    tools = as_gemini_tools(TOOL_DEFINITIONS[:2])
    assert len(tools) == 1
    declarations = tools[0]["functionDeclarations"]
    assert len(declarations) == 2
    assert declarations[0]["name"] == TOOL_DEFINITIONS[0]["name"]
