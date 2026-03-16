import json
from datetime import date

from app.schema.contracts import ChatRequest


def estimate_tokens(value: str) -> int:
    return max(1, len(value) // 4)


def build_system_prompt(request: ChatRequest) -> str:
    ctx = request.project_context
    today = date.today()
    total = len(ctx.tasks)
    overdue = sum(1 for t in ctx.tasks if t.percent_complete < 100 and t.finish_date < today)
    in_progress = sum(1 for t in ctx.tasks if 0 < t.percent_complete < 100)
    completed = sum(1 for t in ctx.tasks if t.percent_complete >= 100)

    return (
        f'You are Sophikon AI - a project management assistant for "{ctx.name}".\n'
        f"Today: {today}\n"
        f"Project status: {ctx.status} | "
        f"{total} tasks | {completed} completed | {in_progress} in progress | {overdue} overdue\n\n"
        "You have tools to read and act on project data:\n"
        "- Read tools (get_tasks, get_dependencies, etc.): use freely, no approval needed.\n"
        "- Write tools (create_task, update_task, etc.): execute directly unless user restricted them.\n"
        "- Delete tools: ALWAYS require user approval - describe clearly what will be deleted.\n"
        "- UI tools (navigate, highlight_tasks, etc.): execute directly to guide the user.\n\n"
        "Be concise and action-oriented. Show your reasoning. Confirm actions you take.\n"
        "When creating multiple tasks at once, use bulk_create_tasks - not one-by-one.\n"
        "After structural changes (create, delete, reorder), call calculate_schedule to keep dates accurate."
    )


def stringify_content(value: str | list[dict]) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def chunk_text(value: str, chunk_size: int = 48) -> list[str]:
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]
