import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.service.agent.tool_registry import (
    DESTRUCTIVE_TOOLS,
    TOOL_SCHEMAS,
    UI_TOOLS,
    ToolResult,
    execute_tool,
)

# ---------------------------------------------------------------------------
# TOOL_SCHEMAS structure
# ---------------------------------------------------------------------------


def test_tool_schemas_contains_all_required_tools():
    names = {t["name"] for t in TOOL_SCHEMAS}

    read_tools = {
        "get_project_summary",
        "get_tasks",
        "get_task",
        "search_tasks",
        "get_dependencies",
        "get_critical_path",
        "get_members",
        "get_resources",
        "get_utilization",
        "get_assignments",
        "get_activity_log",
        "get_comments",
        "get_calendar",
        "get_insights",
    }
    write_tools = {
        "create_task",
        "bulk_create_tasks",
        "update_task",
        "add_dependency",
        "indent_task",
        "outdent_task",
        "reorder_task",
        "calculate_schedule",
        "assign_resource",
        "unassign_resource",
        "post_comment",
        "send_notification",
    }
    destructive_tools = {"delete_task", "delete_dependency"}
    ui_tools = {"navigate", "highlight_tasks", "open_task", "filter_view"}

    expected = read_tools | write_tools | destructive_tools | ui_tools
    missing = expected - names
    assert not missing, f"Missing tools: {missing}"


def test_each_tool_schema_has_required_keys():
    for schema in TOOL_SCHEMAS:
        assert "name" in schema, f"Schema missing 'name': {schema}"
        assert "description" in schema, (
            f"Schema missing 'description' for {schema.get('name')}"
        )
        assert "input_schema" in schema, (
            f"Schema missing 'input_schema' for {schema.get('name')}"
        )


def test_search_tasks_schema_matches_new_contract():
    search_schema = next(t for t in TOOL_SCHEMAS if t["name"] == "search_tasks")
    properties = search_schema["input_schema"]["properties"]
    assert "query" in properties
    assert "status" in properties
    assert "include_parents" in properties
    assert "limit" in properties
    assert "in_progress_only" not in properties
    assert search_schema["input_schema"].get("required") == ["query"]


def test_destructive_tools_set():
    assert "delete_task" in DESTRUCTIVE_TOOLS
    assert "delete_dependency" in DESTRUCTIVE_TOOLS
    assert "create_task" not in DESTRUCTIVE_TOOLS


def test_ui_tools_set():
    assert "navigate" in UI_TOOLS
    assert "highlight_tasks" in UI_TOOLS
    assert "open_task" in UI_TOOLS
    assert "filter_view" in UI_TOOLS


# ---------------------------------------------------------------------------
# ToolResult
# ---------------------------------------------------------------------------


def test_tool_result_success_serializes_data():
    result = ToolResult(success=True, data={"tasks": [{"id": "abc"}]})
    content = json.loads(result.to_content())
    assert content == {"tasks": [{"id": "abc"}]}


def test_tool_result_failure_serializes_error():
    result = ToolResult(success=False, error="Task not found")
    content = json.loads(result.to_content())
    assert content == {"error": "Task not found"}


def test_tool_result_failure_fallback_message():
    result = ToolResult(success=False)
    content = json.loads(result.to_content())
    assert "error" in content


def test_tool_result_is_ui_action_defaults_false():
    result = ToolResult(success=True)
    assert result.is_ui_action is False


# ---------------------------------------------------------------------------
# execute_tool dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_tool_returns_error_for_unknown_tool():
    ctx = MagicMock()
    ctx.db = AsyncMock()
    ctx.project = MagicMock()

    result = await execute_tool("nonexistent_tool", {}, ctx)

    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_execute_tool_ui_tools_return_is_ui_action():
    ctx = MagicMock()
    ctx.db = AsyncMock()
    ctx.project = MagicMock()

    result = await execute_tool("navigate", {"view": "gantt"}, ctx)

    assert result.success is True
    assert result.is_ui_action is True


@pytest.mark.asyncio
async def test_execute_tool_search_tasks_invalid_status_returns_error():
    ctx = MagicMock()
    ctx.db = AsyncMock()
    ctx.project = MagicMock()

    result = await execute_tool(
        "search_tasks",
        {"query": "alpha", "status": "INVALID_STATUS"},
        ctx,
    )

    assert result.success is False
    assert result.error is not None
