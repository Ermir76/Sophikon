"""
Unit tests for calendar_utils.

Pure-Python tests — no database or async required.
"""

from datetime import date

from app.service.calendar_utils import (
    DEFAULT_WORK_WEEK,
    add_working_duration,
    get_working_minutes_for_day,
    is_working_day,
    next_working_day,
    subtract_working_duration,
    working_days_between,
    working_minutes_between,
)

# ── Fixtures ──


class FakeException:
    """Minimal stand-in for CalendarException to avoid importing ORM models."""

    def __init__(self, start_date, end_date, is_working, work_times=None):
        self.start_date = start_date
        self.end_date = end_date
        self.is_working = is_working
        self.work_times = work_times


# ── get_working_minutes_for_day ──


def test_working_minutes_standard_day():
    """8h day with 1h lunch break = 420 working minutes."""
    day = {
        "start": "09:00",
        "end": "17:00",
        "breaks": [{"start": "12:00", "end": "13:00"}],
    }
    assert get_working_minutes_for_day(day) == 420


def test_working_minutes_no_breaks():
    """8h day without breaks = 480 minutes."""
    day = {"start": "09:00", "end": "17:00", "breaks": []}
    assert get_working_minutes_for_day(day) == 480


def test_working_minutes_non_working():
    """None entry = 0 minutes."""
    assert get_working_minutes_for_day(None) == 0


def test_working_minutes_no_breaks_key():
    """Day entry without breaks key = full window."""
    day = {"start": "08:00", "end": "16:00"}
    assert get_working_minutes_for_day(day) == 480


# ── is_working_day ──


def test_is_working_day_monday():
    """Monday (2024-01-01) is a working day in the default work week."""
    assert is_working_day(date(2024, 1, 1), DEFAULT_WORK_WEEK) is True


def test_is_working_day_saturday():
    """Saturday is non-working in the default work week."""
    assert is_working_day(date(2024, 1, 6), DEFAULT_WORK_WEEK) is False


def test_is_working_day_sunday():
    """Sunday is non-working in the default work week."""
    assert is_working_day(date(2024, 1, 7), DEFAULT_WORK_WEEK) is False


def test_is_working_day_holiday_exception():
    """A non-working exception overrides a normally working day."""
    holiday = FakeException(date(2024, 1, 1), date(2024, 1, 1), is_working=False)
    assert is_working_day(date(2024, 1, 1), DEFAULT_WORK_WEEK, [holiday]) is False


def test_is_working_day_working_exception():
    """A working exception makes a normally non-working day into a working day."""
    special = FakeException(date(2024, 1, 6), date(2024, 1, 6), is_working=True)
    assert is_working_day(date(2024, 1, 6), DEFAULT_WORK_WEEK, [special]) is True


# ── add_working_duration ──


def test_add_duration_single_day():
    """420 min (one work day) from Monday → finishes Monday."""
    result = add_working_duration(date(2024, 1, 1), 420, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 1)  # Finishes within Monday


def test_add_duration_two_days():
    """840 min (two work days) from Monday → finishes Tuesday."""
    result = add_working_duration(date(2024, 1, 1), 840, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 2)


def test_add_duration_spans_weekend():
    """Duration spanning Fri → Mon (skips Sat/Sun)."""
    # 2024-01-05 = Friday
    result = add_working_duration(date(2024, 1, 5), 840, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 8)  # Monday


def test_add_duration_zero():
    """Zero duration (milestone) returns same date."""
    result = add_working_duration(date(2024, 1, 1), 0, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 1)


# ── subtract_working_duration ──


def test_subtract_duration_single_day():
    """420 min backwards from Tuesday → starts Tuesday."""
    result = subtract_working_duration(date(2024, 1, 2), 420, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 2)


def test_subtract_duration_spans_weekend():
    """Duration going backwards past weekend (Mon → Fri)."""
    result = subtract_working_duration(date(2024, 1, 8), 840, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 5)  # Friday


def test_subtract_duration_zero():
    """Zero duration returns same date."""
    result = subtract_working_duration(date(2024, 1, 2), 0, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 2)


# ── next_working_day ──


def test_next_working_day_already_working():
    """Monday stays Monday."""
    assert next_working_day(date(2024, 1, 1), DEFAULT_WORK_WEEK) == date(2024, 1, 1)


def test_next_working_day_saturday():
    """Saturday advances to Monday."""
    assert next_working_day(date(2024, 1, 6), DEFAULT_WORK_WEEK) == date(2024, 1, 8)


def test_next_working_day_sunday():
    """Sunday advances to Monday."""
    assert next_working_day(date(2024, 1, 7), DEFAULT_WORK_WEEK) == date(2024, 1, 8)


# ── working_days_between ──


def test_working_minutes_between_same_day():
    """Same working day = that day's minutes."""
    total = working_minutes_between(
        date(2024, 1, 1), date(2024, 1, 1), DEFAULT_WORK_WEEK
    )
    assert total == 420  # Mon-Fri has 420 min/day


def test_working_minutes_between_week():
    """Full work week (Mon-Fri) = 5 × 420 minutes."""
    total = working_minutes_between(
        date(2024, 1, 1), date(2024, 1, 5), DEFAULT_WORK_WEEK
    )
    assert total == 5 * 420


def test_working_minutes_between_spans_weekend():
    """Mon to next Mon (8 calendar days) = 6 working days."""
    total = working_minutes_between(
        date(2024, 1, 1), date(2024, 1, 8), DEFAULT_WORK_WEEK
    )
    assert total == 6 * 420


def test_working_minutes_between_inverted():
    """Start > end returns 0."""
    total = working_minutes_between(
        date(2024, 1, 5), date(2024, 1, 1), DEFAULT_WORK_WEEK
    )
    assert total == 0


def test_working_days_between_alias_matches_minutes_function():
    """Legacy alias is preserved and returns the same value."""
    total_alias = working_days_between(
        date(2024, 1, 1), date(2024, 1, 5), DEFAULT_WORK_WEEK
    )
    total_new = working_minutes_between(
        date(2024, 1, 1), date(2024, 1, 5), DEFAULT_WORK_WEEK
    )
    assert total_alias == total_new
