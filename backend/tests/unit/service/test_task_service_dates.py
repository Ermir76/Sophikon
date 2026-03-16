from datetime import date

from app.service.task_service import _compute_initial_finish_date


def test_compute_initial_finish_date_same_day_for_one_workday() -> None:
    finish_date = _compute_initial_finish_date(
        start_date=date(2024, 1, 1),
        duration_minutes=480,
        is_milestone=False,
        minutes_per_day=480,
    )
    assert finish_date == date(2024, 1, 1)


def test_compute_initial_finish_date_next_day_for_two_workdays() -> None:
    finish_date = _compute_initial_finish_date(
        start_date=date(2024, 1, 1),
        duration_minutes=960,
        is_milestone=False,
        minutes_per_day=480,
    )
    assert finish_date == date(2024, 1, 2)


def test_compute_initial_finish_date_uses_ceiling_day_math() -> None:
    finish_date = _compute_initial_finish_date(
        start_date=date(2024, 1, 1),
        duration_minutes=481,
        is_milestone=False,
        minutes_per_day=480,
    )
    assert finish_date == date(2024, 1, 2)


def test_compute_initial_finish_date_milestone_stays_same_day() -> None:
    finish_date = _compute_initial_finish_date(
        start_date=date(2024, 1, 1),
        duration_minutes=0,
        is_milestone=True,
        minutes_per_day=480,
    )
    assert finish_date == date(2024, 1, 1)
