"""
Versioned prompt builders for agent runs.
"""

from app.service.agent.context import AgentContext

PROMPT_VERSION = "1"

_DOMAIN_KNOWLEDGE = (
    "Sophikon domain rules:",
    "- Task status values are BACKLOG, TODO, IN_PROGRESS, IN_REVIEW, DONE.",
    "- Use WBS-aware operations for hierarchy changes (indent, outdent, reorder).",
    "- After structural changes (tasks/dependencies), run calculate_schedule.",
    "- Use bulk_create_tasks when creating many tasks in one request.",
    "- Ask for approval before destructive actions and include a clear reason.",
)


def build_prompt_cache_metadata(scope: str) -> dict:
    return {
        "key": f"agent:{scope}:v{PROMPT_VERSION}",
        "ttl_seconds": 3600,
        "tags": ["agent", scope, f"v{PROMPT_VERSION}"],
    }


def build_planner_system_prompt() -> str:
    return (
        "You are a professional Project Manager AI assistant. "
        "Your ONLY task right now is to produce a concise, numbered plan for the user's request. "
        "Do NOT execute anything. Do NOT call any other tools. "
        "Call define_plan exactly once with your proposed steps and whether execution is needed.\n\n"
        + "\n".join(_DOMAIN_KNOWLEDGE)
    )


def build_execution_system_prompt(ctx: AgentContext, memory: str | None) -> str:
    project = ctx.project
    parts = [
        f"Prompt version: {PROMPT_VERSION}",
        f"You are a professional Project Manager AI assistant for the project '{project.name}'.",
        f"Project status: {project.status}",
        f"Start date: {project.start_date}",
    ]
    if project.finish_date:
        parts.append(f"Finish date: {project.finish_date}")
    if project.description:
        parts.append(f"Description: {project.description}")

    parts.append(
        "\nYou have access to tools to read and modify the project. "
        "When taking actions, prefer bulk operations over repeated single calls."
    )
    parts.append("\n".join(_DOMAIN_KNOWLEDGE))

    if memory:
        parts.append(
            f"\n[Project memory - key decisions and preferences from past sessions]\n{memory}"
        )

    return "\n".join(parts)


def build_proactive_system_prompt(project_name: str, memory: str | None) -> str:
    prompt = (
        f"Prompt version: {PROMPT_VERSION}\n"
        f"You are a proactive project health monitor for '{project_name}'. "
        "Analyze the project data provided and identify actionable issues "
        "(overdue tasks, critical path delays, serious risks). "
        "If issues are found, start your response with 'ISSUES FOUND:' and list them concisely in markdown. "
        "If the project is on track with no significant issues, respond only with 'NO ISSUES'.\n\n"
        + "\n".join(_DOMAIN_KNOWLEDGE)
    )
    if not memory:
        return prompt
    return f"{prompt}\n\nProject memory:\n{memory}"
