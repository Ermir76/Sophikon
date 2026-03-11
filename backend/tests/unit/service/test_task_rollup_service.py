from datetime import date

import pytest
from uuid_utils import uuid7

from app.core.exceptions import ValidationError
from app.models.task import Task
from app.service.calendar_utils import DEFAULT_WORK_WEEK
from app.service.task_rollup_service import (
    apply_summary_rollup,
    clear_summary_rollup,
    sync_leaf_duration_progress,
    validate_summary_rollup_edit,
)


def _build_task(
    *,
    name: str,
    start_date: date,
    finish_date: date,
    duration: int,
    **overrides,
) -> Task:
    data = {
        "project_id": uuid7(),
        "wbs_code": "1",
        "outline_level": 1,
        "order_index": 1,
        "name": name,
        "start_date": start_date,
        "finish_date": finish_date,
        "duration": duration,
        "work": duration,
        "actual_duration": 0,
        "remaining_duration": duration,
        "actual_work": 0,
        "remaining_work": duration,
        "percent_complete": 0.0,
        "percent_work_complete": 0.0,
        "actual_start": None,
        "actual_finish": None,
        "actual_cost": 0.0,
        "total_cost": 0.0,
        "remaining_cost": 0.0,
        "is_summary": False,
        "is_critical": False,
        "total_slack": 0,
        "free_slack": 0,
    }
    data.update(overrides)
    return Task(**data)


def test_sync_leaf_duration_progress_sets_actual_and_remaining_minutes() -> None:
    task = _build_task(
        name="Leaf",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 2),
        duration=960,  # 2 working days (2 * 480min)
        percent_complete=25.0,
    )

    sync_leaf_duration_progress(task)

    assert task.actual_duration == 240
    assert task.remaining_duration == 720


def test_sync_leaf_duration_progress_clamps_percent_out_of_bounds() -> None:
    over_complete = _build_task(
        name="Over Complete",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
        percent_complete=150.0,
    )
    under_complete = _build_task(
        name="Under Complete",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
        percent_complete=-10.0,
    )

    sync_leaf_duration_progress(over_complete)
    sync_leaf_duration_progress(under_complete)

    assert over_complete.actual_duration == 480
    assert over_complete.remaining_duration == 0
    assert under_complete.actual_duration == 0
    assert under_complete.remaining_duration == 480


def test_apply_summary_rollup_aggregates_dates_progress_costs_and_critical() -> None:
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
    )
    child_a = _build_task(
        name="Child A",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
        work=480,
        actual_duration=240,
        remaining_duration=240,
        actual_work=240,
        remaining_work=240,
        percent_complete=50.0,
        actual_start=date(2024, 1, 1),
        actual_finish=date(2024, 1, 1),
        actual_cost=100.0,
        total_cost=200.0,
        remaining_cost=100.0,
        is_critical=False,
        total_slack=480,
    )
    child_b = _build_task(
        name="Child B",
        start_date=date(2024, 1, 2),
        finish_date=date(2024, 1, 3),
        duration=960,  # 2 working days (2 * 480min)
        work=960,
        actual_duration=960,
        remaining_duration=0,
        actual_work=960,
        remaining_work=0,
        percent_complete=100.0,
        actual_start=date(2024, 1, 2),
        actual_finish=date(2024, 1, 3),
        actual_cost=300.0,
        total_cost=450.0,
        remaining_cost=150.0,
        is_critical=True,
        total_slack=0,
    )

    apply_summary_rollup(summary, [child_a, child_b], DEFAULT_WORK_WEEK, [])

    assert summary.start_date == date(2024, 1, 1)
    assert summary.finish_date == date(2024, 1, 3)
    assert summary.duration == 1440
    assert summary.work == 1440
    assert summary.actual_duration == 1200
    assert summary.remaining_duration == 240
    assert summary.actual_work == 1200
    assert summary.remaining_work == 240
    assert summary.percent_complete == pytest.approx(83.333333, rel=1e-6)
    assert summary.percent_work_complete == pytest.approx(83.333333, rel=1e-6)
    assert summary.actual_start == date(2024, 1, 1)
    assert summary.actual_finish == date(2024, 1, 3)
    assert summary.actual_cost == 400.0
    assert summary.total_cost == 650.0
    assert summary.remaining_cost == 250.0
    assert summary.is_critical is True
    assert summary.total_slack == 0
    assert summary.free_slack == 0


def test_clear_summary_rollup_resets_computed_fields() -> None:
    summary = _build_task(
        name="Summary To Clear",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 2),
        duration=960,
        is_summary=True,
        work=960,
        actual_duration=480,
        remaining_duration=480,
        actual_work=480,
        remaining_work=480,
        percent_complete=50.0,
        percent_work_complete=50.0,
        actual_start=date(2024, 1, 1),
        actual_finish=date(2024, 1, 2),
        actual_cost=100.0,
        total_cost=200.0,
        remaining_cost=100.0,
        is_critical=True,
        total_slack=120,
        free_slack=60,
    )

    clear_summary_rollup(summary, DEFAULT_WORK_WEEK, [])

    assert summary.is_summary is False
    assert summary.duration == 960
    assert summary.actual_duration == 0
    assert summary.remaining_duration == 0
    assert summary.work == 0
    assert summary.actual_work == 0
    assert summary.remaining_work == 0
    assert summary.percent_complete == 0.0
    assert summary.percent_work_complete == 0.0
    assert summary.actual_start is None
    assert summary.actual_finish is None
    assert summary.actual_cost == 0.0
    assert summary.total_cost == 0.0
    assert summary.remaining_cost == 0.0
    assert summary.is_critical is False
    assert summary.total_slack == 0
    assert summary.free_slack == 0


def test_validate_summary_rollup_edit_blocks_computed_fields() -> None:
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,
        is_summary=True,
    )
    leaf = _build_task(
        name="Leaf",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,
        is_summary=False,
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_summary_rollup_edit(summary, {"duration": 960, "name": "Renamed"})
    assert "duration" in str(exc_info.value)

    validate_summary_rollup_edit(summary, {"name": "Renamed"})
    validate_summary_rollup_edit(leaf, {"duration": 960})
