"""
Calendar utilities for working-day arithmetic.

Converts task durations (in minutes) to calendar dates by respecting
working days, working hours, and calendar exceptions (holidays).
"""

from datetime import date, timedelta

from app.models.calendar_exception import CalendarException

# Default standard work week (Mon-Fri 09:00-17:00, 8h/day).
# Sunday=0, Saturday=6
DEFAULT_WORK_WEEK: list[dict | None] = [
    None,  # Sunday
    {"start": "09:00", "end": "17:00", "breaks": []},
    {"start": "09:00", "end": "17:00", "breaks": []},
    {"start": "09:00", "end": "17:00", "breaks": []},
    {"start": "09:00", "end": "17:00", "breaks": []},
    {"start": "09:00", "end": "17:00", "breaks": []},
    None,  # Saturday
]


def get_working_minutes_for_day(day_entry: dict | None) -> int:
    """
    Extract total working minutes from a single day-of-week entry.

    Returns 0 for non-working days (None entries).
    Subtracts break durations from total work window.
    """
    if day_entry is None:
        return 0

    start_h, start_m = map(int, day_entry["start"].split(":"))
    end_h, end_m = map(int, day_entry["end"].split(":"))
    total = (end_h * 60 + end_m) - (start_h * 60 + start_m)

    for brk in day_entry.get("breaks", []):
        brk_start_h, brk_start_m = map(int, brk["start"].split(":"))
        brk_end_h, brk_end_m = map(int, brk["end"].split(":"))
        total -= (brk_end_h * 60 + brk_end_m) - (brk_start_h * 60 + brk_start_m)

    return max(total, 0)


def _date_to_weekday_index(d: date) -> int:
    """Convert a Python date to work_week index (Sunday=0, Saturday=6)."""
    # Python: Monday=0 .. Sunday=6
    # Calendar JSONB: Sunday=0 .. Saturday=6
    return (d.weekday() + 1) % 7


def is_working_day(
    d: date,
    work_week: list[dict | None],
    exceptions: list[CalendarException] | None = None,
) -> bool:
    """
    Check if a specific date is a working day.

    Calendar exceptions override the normal work_week pattern:
    - Non-working exceptions (is_working=False) turn a working day into a holiday.
    - Working exceptions (is_working=True) turn a non-working day into a working day.
    """
    # Check exceptions first — they override the weekly pattern
    if exceptions:
        for exc in exceptions:
            if exc.start_date <= d <= exc.end_date:
                return exc.is_working

    idx = _date_to_weekday_index(d)
    return work_week[idx] is not None


def get_working_minutes_on_date(
    d: date,
    work_week: list[dict | None],
    exceptions: list[CalendarException] | None = None,
) -> int:
    """
    Get the number of working minutes for a specific date.

    Respects calendar exceptions with custom work_times.
    """
    if exceptions:
        for exc in exceptions:
            if exc.start_date <= d <= exc.end_date:
                if not exc.is_working:
                    return 0
                # Working exception with custom hours
                if exc.work_times:
                    return get_working_minutes_for_day(exc.work_times)
                # Working exception without custom hours — use normal day pattern
                break

    idx = _date_to_weekday_index(d)
    return get_working_minutes_for_day(work_week[idx])


def add_working_duration(
    start_date: date,
    duration_minutes: int,
    work_week: list[dict | None],
    exceptions: list[CalendarException] | None = None,
) -> date:
    """
    Compute the finish date by adding a duration (minutes) to a start date.

    Skips non-working days. Duration is consumed in chunks of the daily
    working minutes for each working day.

    Returns start_date for zero-duration (milestones).
    """
    if duration_minutes <= 0:
        return start_date

    remaining = duration_minutes
    current = start_date

    # Safety limit to prevent infinite loops on misconfigured calendars
    max_iterations = duration_minutes + 365
    iterations = 0

    while remaining > 0 and iterations < max_iterations:
        daily_minutes = get_working_minutes_on_date(current, work_week, exceptions)

        if daily_minutes > 0:
            if remaining <= daily_minutes:
                # Task finishes on this day
                return current
            remaining -= daily_minutes

        current += timedelta(days=1)
        iterations += 1

    return current


def subtract_working_duration(
    finish_date: date,
    duration_minutes: int,
    work_week: list[dict | None],
    exceptions: list[CalendarException] | None = None,
) -> date:
    """
    Compute the start date by subtracting a duration (minutes) from a finish date.

    Walks backwards through the calendar, skipping non-working days.

    Returns finish_date for zero-duration (milestones).
    """
    if duration_minutes <= 0:
        return finish_date

    remaining = duration_minutes
    current = finish_date

    max_iterations = duration_minutes + 365
    iterations = 0

    while remaining > 0 and iterations < max_iterations:
        daily_minutes = get_working_minutes_on_date(current, work_week, exceptions)

        if daily_minutes > 0:
            if remaining <= daily_minutes:
                return current
            remaining -= daily_minutes

        current -= timedelta(days=1)
        iterations += 1

    return current


def next_working_day(
    d: date,
    work_week: list[dict | None],
    exceptions: list[CalendarException] | None = None,
) -> date:
    """
    Return d if it is a working day, otherwise advance to the next working day.

    Safety-capped at 365 days to prevent infinite loops.
    """
    for _ in range(365):
        if is_working_day(d, work_week, exceptions):
            return d
        d += timedelta(days=1)
    return d


def working_minutes_between(
    start: date,
    end: date,
    work_week: list[dict | None],
    exceptions: list[CalendarException] | None = None,
) -> int:
    """
    Count the total working minutes between two dates (inclusive).

    Useful for computing slack in working minutes.
    """
    if start > end:
        return 0

    total = 0
    current = start
    while current <= end:
        total += get_working_minutes_on_date(current, work_week, exceptions)
        current += timedelta(days=1)
    return total


# Backward-compatible alias: historical name kept temporarily.
def working_days_between(
    start: date,
    end: date,
    work_week: list[dict | None],
    exceptions: list[CalendarException] | None = None,
) -> int:
    return working_minutes_between(start, end, work_week, exceptions)
