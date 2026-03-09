from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ValidationError
from app.models.calendar import Calendar
from app.models.calendar_exception import CalendarException
from app.models.project import Project
from app.models.task import Task
from app.service.calendar_utils import DEFAULT_WORK_WEEK, working_minutes_between

SUMMARY_ROLLUP_EDIT_FIELDS = frozenset(
    {
        "start_date",
        "finish_date",
        "duration",
        "percent_complete",
    }
)


def _to_decimal(value: Decimal | float | int | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def sync_leaf_duration_progress(task: Task) -> None:
    """
    Keep leaf duration progress fields derived from duration + percent_complete.

    actual_duration and remaining_duration are persisted integer minute fields.
    """
    duration = max(task.duration, 0)
    percent_complete = _to_decimal(task.percent_complete)
    percent_complete = min(max(percent_complete, Decimal("0")), Decimal("100"))
    actual_duration = int(
        ((Decimal(duration) * percent_complete) / Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    task.actual_duration = min(actual_duration, duration)
    task.remaining_duration = max(duration - task.actual_duration, 0)


async def load_project_rollup_calendar(
    db: AsyncSession,
    project: Project,
) -> tuple[list[dict | None], list[CalendarException]]:
    if not project.default_calendar_id:
        return DEFAULT_WORK_WEEK, []

    result = await db.execute(
        select(Calendar)
        .options(selectinload(Calendar.exceptions))
        .where(Calendar.id == project.default_calendar_id)
    )
    calendar = result.scalar_one_or_none()
    if not calendar:
        return DEFAULT_WORK_WEEK, []

    return calendar.work_week, list(calendar.exceptions)


def calculate_summary_duration_minutes(
    start_date,
    finish_date,
    work_week: list[dict | None],
    exceptions: list[CalendarException],
) -> int:
    return working_minutes_between(start_date, finish_date, work_week, exceptions)


def apply_summary_rollup(
    summary: Task,
    children: list[Task],
    work_week: list[dict | None],
    exceptions: list[CalendarException],
) -> None:
    summary.is_summary = True
    summary.start_date = min(child.start_date for child in children)
    summary.finish_date = max(child.finish_date for child in children)
    summary.duration = calculate_summary_duration_minutes(
        summary.start_date,
        summary.finish_date,
        work_week,
        exceptions,
    )

    summary.work = sum(child.work for child in children)
    summary.actual_duration = sum(child.actual_duration for child in children)
    summary.remaining_duration = sum(child.remaining_duration for child in children)
    summary.actual_work = sum(child.actual_work for child in children)
    summary.remaining_work = sum(child.remaining_work for child in children)

    total_duration = sum(child.duration for child in children)
    if total_duration > 0:
        weighted_percent = sum(
            _to_decimal(child.percent_complete) * child.duration for child in children
        ) / Decimal(total_duration)
        summary.percent_complete = float(weighted_percent)
    else:
        summary.percent_complete = 0.0

    if summary.work > 0:
        percent_work_complete = (
            Decimal(summary.actual_work) / Decimal(summary.work)
        ) * Decimal("100")
        summary.percent_work_complete = float(percent_work_complete)
    else:
        summary.percent_work_complete = 0.0

    actual_starts = [
        child.actual_start for child in children if child.actual_start is not None
    ]
    summary.actual_start = min(actual_starts) if actual_starts else None
    actual_finishes = [
        child.actual_finish for child in children if child.actual_finish is not None
    ]
    if len(actual_finishes) == len(children):
        summary.actual_finish = max(actual_finishes)
    else:
        summary.actual_finish = None

    summary.actual_cost = float(
        sum(
            (_to_decimal(child.actual_cost) for child in children),
            Decimal("0"),
        )
    )
    summary.total_cost = float(
        sum(
            (_to_decimal(child.total_cost) for child in children),
            Decimal("0"),
        )
    )
    summary.remaining_cost = float(
        sum(
            (_to_decimal(child.remaining_cost) for child in children),
            Decimal("0"),
        )
    )

    summary.is_critical = any(bool(child.is_critical) for child in children)
    if summary.is_critical:
        summary.total_slack = 0
    else:
        summary.total_slack = min(child.total_slack for child in children)
    summary.free_slack = 0


def clear_summary_rollup(
    summary: Task,
    work_week: list[dict | None],
    exceptions: list[CalendarException],
) -> None:
    summary.is_summary = False
    # TODO(2026-03-07): Decide whether ex-summary tasks should keep rolled-up snapshot
    # dates or reset to explicit leaf defaults when the last child is removed.
    summary.duration = calculate_summary_duration_minutes(
        summary.start_date,
        summary.finish_date,
        work_week,
        exceptions,
    )
    summary.actual_duration = 0
    summary.remaining_duration = 0
    summary.work = 0
    summary.actual_work = 0
    summary.remaining_work = 0
    summary.percent_complete = 0.0
    summary.percent_work_complete = 0.0
    summary.actual_start = None
    summary.actual_finish = None
    summary.actual_cost = 0.0
    summary.total_cost = 0.0
    summary.remaining_cost = 0.0
    summary.is_critical = False
    summary.total_slack = 0
    summary.free_slack = 0


def validate_summary_rollup_edit(task: Task, update_data: dict) -> None:
    blocked_fields = sorted(SUMMARY_ROLLUP_EDIT_FIELDS & update_data.keys())
    if task.is_summary and blocked_fields:
        joined_fields = ", ".join(blocked_fields)
        raise ValidationError(
            f"Summary tasks auto-calculate {joined_fields} from their children"
        )
