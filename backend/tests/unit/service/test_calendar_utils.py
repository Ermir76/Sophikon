"""
Unit tests for calendar_utils.

Pure-Python tests: no database and no async.
"""

from datetime import date

import pytest

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

DEFAULT_DAY_MINUTES = get_working_minutes_for_day(DEFAULT_WORK_WEEK[1])


class FakeException:
    """Minimal stand-in for CalendarException."""

    def __init__(self, start_date, end_date, is_working, work_times=None):
        self.start_date = start_date
        self.end_date = end_date
        self.is_working = is_working
        self.work_times = work_times


def test_working_minutes_standard_day():
    day = {
        "start": "09:00",
        "end": "17:00",
        "breaks": [{"start": "12:00", "end": "13:00"}],
    }
    assert get_working_minutes_for_day(day) == 420


def test_working_minutes_no_breaks():
    day = {"start": "09:00", "end": "17:00", "breaks": []}
    assert get_working_minutes_for_day(day) == 480


def test_working_minutes_non_working():
    assert get_working_minutes_for_day(None) == 0


def test_working_minutes_no_breaks_key():
    day = {"start": "08:00", "end": "16:00"}
    assert get_working_minutes_for_day(day) == 480


def test_is_working_day_monday():
    assert is_working_day(date(2024, 1, 1), DEFAULT_WORK_WEEK) is True


def test_is_working_day_saturday():
    assert is_working_day(date(2024, 1, 6), DEFAULT_WORK_WEEK) is False


def test_is_working_day_sunday():
    assert is_working_day(date(2024, 1, 7), DEFAULT_WORK_WEEK) is False


def test_is_working_day_holiday_exception():
    holiday = FakeException(date(2024, 1, 1), date(2024, 1, 1), is_working=False)
    assert is_working_day(date(2024, 1, 1), DEFAULT_WORK_WEEK, [holiday]) is False


def test_is_working_day_working_exception():
    special = FakeException(date(2024, 1, 6), date(2024, 1, 6), is_working=True)
    assert is_working_day(date(2024, 1, 6), DEFAULT_WORK_WEEK, [special]) is True


def test_add_duration_single_day():
    result = add_working_duration(
        date(2024, 1, 1), DEFAULT_DAY_MINUTES, DEFAULT_WORK_WEEK
    )
    assert result == date(2024, 1, 1)


def test_add_duration_two_days():
    result = add_working_duration(
        date(2024, 1, 1),
        DEFAULT_DAY_MINUTES * 2,
        DEFAULT_WORK_WEEK,
    )
    assert result == date(2024, 1, 2)


def test_add_duration_spans_weekend():
    result = add_working_duration(
        date(2024, 1, 5),  # Friday
        DEFAULT_DAY_MINUTES * 2,
        DEFAULT_WORK_WEEK,
    )
    assert result == date(2024, 1, 8)  # Monday


def test_add_duration_zero():
    result = add_working_duration(date(2024, 1, 1), 0, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 1)


def test_subtract_duration_single_day():
    result = subtract_working_duration(
        date(2024, 1, 2), DEFAULT_DAY_MINUTES, DEFAULT_WORK_WEEK
    )
    assert result == date(2024, 1, 2)


def test_subtract_duration_spans_weekend():
    result = subtract_working_duration(
        date(2024, 1, 8),
        DEFAULT_DAY_MINUTES * 2,
        DEFAULT_WORK_WEEK,
    )
    assert result == date(2024, 1, 5)  # Friday


def test_subtract_duration_zero():
    result = subtract_working_duration(date(2024, 1, 2), 0, DEFAULT_WORK_WEEK)
    assert result == date(2024, 1, 2)


def test_next_working_day_already_working():
    assert next_working_day(date(2024, 1, 1), DEFAULT_WORK_WEEK) == date(2024, 1, 1)


def test_next_working_day_saturday():
    assert next_working_day(date(2024, 1, 6), DEFAULT_WORK_WEEK) == date(2024, 1, 8)


def test_next_working_day_sunday():
    assert next_working_day(date(2024, 1, 7), DEFAULT_WORK_WEEK) == date(2024, 1, 8)


def test_working_minutes_between_same_day():
    total = working_minutes_between(
        date(2024, 1, 1), date(2024, 1, 1), DEFAULT_WORK_WEEK
    )
    assert total == DEFAULT_DAY_MINUTES


def test_working_minutes_between_week():
    total = working_minutes_between(
        date(2024, 1, 1), date(2024, 1, 5), DEFAULT_WORK_WEEK
    )
    assert total == 5 * DEFAULT_DAY_MINUTES


def test_working_minutes_between_spans_weekend():
    total = working_minutes_between(
        date(2024, 1, 1), date(2024, 1, 8), DEFAULT_WORK_WEEK
    )
    assert total == 6 * DEFAULT_DAY_MINUTES


def test_working_minutes_between_inverted():
    with pytest.raises(ValueError, match="start .* is after end"):
        working_minutes_between(date(2024, 1, 5), date(2024, 1, 1), DEFAULT_WORK_WEEK)


def test_working_days_between_alias_matches_minutes_function():
    total_alias = working_days_between(
        date(2024, 1, 1), date(2024, 1, 5), DEFAULT_WORK_WEEK
    )
    total_new = working_minutes_between(
        date(2024, 1, 1), date(2024, 1, 5), DEFAULT_WORK_WEEK
    )
    assert total_alias == total_new
