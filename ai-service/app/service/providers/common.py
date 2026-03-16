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

    lines: list[str] = [
        f'You are Sophikon AI - a project management assistant for "{ctx.name}".',
        f"Today: {today}",
        f"Project: {ctx.status} | starts {ctx.start_date}"
        + (f" → ends {ctx.finish_date}" if ctx.finish_date else ""),
    ]

    if ctx.description:
        lines.append(f"Description: {ctx.description}")

    lines.append(
        f"Tasks: {total} total | {completed} completed | {in_progress} in progress | {overdue} overdue"
    )

    if ctx.tasks:
        lines.append("")
        lines.append(f"Current task list ({total} tasks):")
        for t in ctx.tasks[:80]:
            status = "✓" if t.percent_complete >= 100 else ("⚠ OVERDUE" if t.finish_date < today else f"{int(t.percent_complete)}%")
            kind = " [summary]" if t.is_summary else ""
            lines.append(
                f"  [{t.id}] {t.name}{kind} — {status} — {t.start_date} → {t.finish_date}"
            )
        if total > 80:
            lines.append(f"  ... and {total - 80} more tasks (use get_tasks tool to see all)")

    lines += [
        "",
        "You have tools to read and act on project data:",
        "- Read tools (get_tasks, get_dependencies, etc.): use freely, no approval needed.",
        "- Write tools (create_task, update_task, etc.): execute directly unless user restricted them.",
        "- Delete tools: ALWAYS require user approval - describe clearly what will be deleted.",
        "- UI tools (navigate, highlight_tasks, etc.): execute directly to guide the user.",
        "",
        "Be concise and action-oriented. Show your reasoning. Confirm actions you take.",
        "When creating multiple tasks at once, use bulk_create_tasks - not one-by-one.",
        "After structural changes (create, delete, reorder), call calculate_schedule to keep dates accurate.",
    ]

    return "\n".join(lines)


def stringify_content(value: str | list[dict]) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def chunk_text(value: str, chunk_size: int = 48) -> list[str]:
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]
