from datetime import date

import pytest
from uuid_utils import uuid7

from app.core.exceptions import ValidationError
from app.models.enums import TaskStatus
from app.models.task import Task
from app.service.calendar_utils import DEFAULT_WORK_WEEK
from app.service.task_rollup_service import (
    apply_summary_rollup,
    clear_summary_rollup,
    sync_leaf_duration_progress,
    validate_summary_rollup_edit,
)
from app.service.task_service import (
    derive_percent_from_status,
    derive_status_from_percent,
    resolve_status_thresholds,
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


def test_apply_summary_rollup_preserves_earned_value_fields_current_behavior() -> None:
    """
    Pass-now behavior: rollup does not recompute EVM fields yet.

    TODO: when EVM rollup semantics are implemented, replace this assertion
    with explicit bcws/bcwp/acwp aggregation rules.
    """
    summary = _build_task(
        name="Summary EVM",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
        bcws=12.0,
        bcwp=34.0,
        acwp=56.0,
    )
    child_a = _build_task(
        name="Child A",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,  # 1 working day (8h * 60min)
        bcws=100.0,
        bcwp=120.0,
        acwp=130.0,
    )
    child_b = _build_task(
        name="Child B",
        start_date=date(2024, 1, 2),
        finish_date=date(2024, 1, 2),
        duration=480,  # 1 working day (8h * 60min)
        bcws=200.0,
        bcwp=220.0,
        acwp=230.0,
    )

    apply_summary_rollup(summary, [child_a, child_b], DEFAULT_WORK_WEEK, [])

    assert summary.bcws == 12.0
    assert summary.bcwp == 34.0
    assert summary.acwp == 56.0


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
    assert summary.start_date == date(2024, 1, 1)
    assert summary.finish_date == date(2024, 1, 1)
    assert summary.duration == 480
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


def test_validate_summary_rollup_edit_blocks_start_and_percent_fields() -> None:
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,
        is_summary=True,
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_summary_rollup_edit(
            summary,
            {"start_date": date(2024, 1, 2), "percent_complete": 50.0},
        )

    message = str(exc_info.value)
    assert "start_date" in message
    assert "percent_complete" in message


def test_validate_summary_rollup_edit_allows_notes_edit_on_summary() -> None:
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,
        is_summary=True,
        notes="Original",
    )

    validate_summary_rollup_edit(summary, {"notes": "Updated"})


def test_apply_summary_rollup_single_child_matches_child_values() -> None:
    summary = _build_task(
        name="Summary Single Child",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
    )
    child = _build_task(
        name="Only Child",
        start_date=date(2024, 1, 4),
        finish_date=date(2024, 1, 5),
        duration=960,  # 2 working days (2 * 480min)
        work=960,
        actual_duration=480,
        remaining_duration=480,
        actual_work=480,
        remaining_work=480,
        percent_complete=50.0,
        actual_start=date(2024, 1, 4),
        actual_finish=None,
        actual_cost=150.0,
        total_cost=220.0,
        remaining_cost=70.0,
        is_critical=False,
        total_slack=480,
    )

    apply_summary_rollup(summary, [child], DEFAULT_WORK_WEEK, [])

    assert summary.start_date == child.start_date
    assert summary.finish_date == child.finish_date
    assert summary.duration == 960
    assert summary.percent_complete == 50.0
    assert summary.actual_cost == 150.0
    assert summary.total_cost == 220.0
    assert summary.remaining_cost == 70.0
    assert summary.total_slack == 480


def test_apply_summary_rollup_all_children_complete_sets_100_percent() -> None:
    summary = _build_task(
        name="Summary Complete",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
    )
    child_a = _build_task(
        name="Done A",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=480,
        work=480,
        actual_duration=480,
        remaining_duration=0,
        actual_work=480,
        remaining_work=0,
        percent_complete=100.0,
        percent_work_complete=100.0,
    )
    child_b = _build_task(
        name="Done B",
        start_date=date(2024, 1, 2),
        finish_date=date(2024, 1, 2),
        duration=480,
        work=480,
        actual_duration=480,
        remaining_duration=0,
        actual_work=480,
        remaining_work=0,
        percent_complete=100.0,
        percent_work_complete=100.0,
    )

    apply_summary_rollup(summary, [child_a, child_b], DEFAULT_WORK_WEEK, [])

    assert summary.percent_complete == 100.0
    assert summary.percent_work_complete == 100.0
    assert summary.remaining_duration == 0
    assert summary.remaining_work == 0


def test_apply_summary_rollup_zero_duration_milestones() -> None:
    summary = _build_task(
        name="Summary Milestones",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
    )
    milestone_a = _build_task(
        name="M1",
        start_date=date(2024, 1, 3),
        finish_date=date(2024, 1, 3),
        duration=0,
        work=0,
        actual_duration=0,
        remaining_duration=0,
        actual_work=0,
        remaining_work=0,
        percent_complete=100.0,
    )
    milestone_b = _build_task(
        name="M2",
        start_date=date(2024, 1, 5),
        finish_date=date(2024, 1, 5),
        duration=0,
        work=0,
        actual_duration=0,
        remaining_duration=0,
        actual_work=0,
        remaining_work=0,
        percent_complete=0.0,
    )

    apply_summary_rollup(summary, [milestone_a, milestone_b], DEFAULT_WORK_WEEK, [])

    assert summary.start_date == date(2024, 1, 3)
    assert summary.finish_date == date(2024, 1, 5)
    assert summary.duration == 1440
    assert summary.percent_complete == 0.0
    assert summary.percent_work_complete == 0.0


def test_apply_summary_rollup_parent_with_mix_of_milestones_and_tasks() -> None:
    summary = _build_task(
        name="Summary Mixed",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
    )
    milestone = _build_task(
        name="Milestone",
        start_date=date(2024, 1, 2),
        finish_date=date(2024, 1, 2),
        duration=0,
        work=0,
        actual_duration=0,
        remaining_duration=0,
        actual_work=0,
        remaining_work=0,
        percent_complete=100.0,
        percent_work_complete=100.0,
    )
    task = _build_task(
        name="Task",
        start_date=date(2024, 1, 3),
        finish_date=date(2024, 1, 4),
        duration=960,  # 2 working days (2 * 480min)
        work=960,
        actual_duration=480,
        remaining_duration=480,
        actual_work=480,
        remaining_work=480,
        percent_complete=50.0,
        percent_work_complete=50.0,
    )

    apply_summary_rollup(summary, [milestone, task], DEFAULT_WORK_WEEK, [])

    assert summary.start_date == date(2024, 1, 2)
    assert summary.finish_date == date(2024, 1, 4)
    assert summary.duration == 1440
    assert summary.percent_complete == 50.0
    assert summary.percent_work_complete == 50.0


def test_resolve_status_thresholds_uses_defaults_for_invalid_values() -> None:
    thresholds = resolve_status_thresholds(
        {"status_thresholds": {"IN_PROGRESS": "bad", "IN_REVIEW": None, "DONE": 200}}
    )

    assert thresholds == {"IN_PROGRESS": 1, "IN_REVIEW": 80, "DONE": 100}


def test_resolve_status_thresholds_clamps_review_below_done() -> None:
    thresholds = resolve_status_thresholds(
        {"status_thresholds": {"IN_PROGRESS": 1, "IN_REVIEW": 100, "DONE": 100}}
    )

    assert thresholds == {"IN_PROGRESS": 1, "IN_REVIEW": 99, "DONE": 100}


def test_derive_status_from_percent_preserves_backlog_and_maps_zero_to_todo() -> None:
    thresholds = resolve_status_thresholds({})

    status_from_backlog = derive_status_from_percent(
        0,
        thresholds,
        current_status=TaskStatus.BACKLOG,
    )
    status_from_in_progress = derive_status_from_percent(
        0,
        thresholds,
        current_status=TaskStatus.IN_PROGRESS,
    )

    assert status_from_backlog == TaskStatus.BACKLOG
    assert status_from_in_progress == TaskStatus.TODO


def test_derive_status_from_percent_honors_explicit_zero_status_override() -> None:
    thresholds = resolve_status_thresholds({})

    explicit_backlog = derive_status_from_percent(
        0,
        thresholds,
        current_status=TaskStatus.TODO,
        explicit_zero_status=TaskStatus.BACKLOG,
    )
    explicit_todo = derive_status_from_percent(
        0,
        thresholds,
        current_status=TaskStatus.BACKLOG,
        explicit_zero_status=TaskStatus.TODO,
    )

    assert explicit_backlog == TaskStatus.BACKLOG
    assert explicit_todo == TaskStatus.TODO


def test_derive_status_from_percent_respects_threshold_boundaries() -> None:
    thresholds = resolve_status_thresholds(
        {"status_thresholds": {"IN_PROGRESS": 1, "IN_REVIEW": 70, "DONE": 95}}
    )

    assert (
        derive_status_from_percent(1, thresholds, current_status=TaskStatus.TODO)
        == TaskStatus.IN_PROGRESS
    )
    assert (
        derive_status_from_percent(70, thresholds, current_status=TaskStatus.TODO)
        == TaskStatus.IN_REVIEW
    )
    assert (
        derive_status_from_percent(95, thresholds, current_status=TaskStatus.TODO)
        == TaskStatus.DONE
    )


def test_derive_percent_from_status_uses_threshold_values() -> None:
    thresholds = {"IN_PROGRESS": 5, "IN_REVIEW": 75, "DONE": 99}

    assert derive_percent_from_status(TaskStatus.BACKLOG, thresholds) == 0.0
    assert derive_percent_from_status(TaskStatus.TODO, thresholds) == 0.0
    assert derive_percent_from_status(TaskStatus.IN_PROGRESS, thresholds) == 5.0
    assert derive_percent_from_status(TaskStatus.IN_REVIEW, thresholds) == 75.0
    assert derive_percent_from_status(TaskStatus.DONE, thresholds) == 99.0


# FEAT-02: summary status derived from rolled-up percent


def _make_child(
    name: str, start: date, finish: date, duration: int, percent: float
) -> Task:
    return _build_task(
        name=name,
        start_date=start,
        finish_date=finish,
        duration=duration,
        work=duration,
        actual_duration=int(duration * percent / 100),
        remaining_duration=duration - int(duration * percent / 100),
        actual_work=int(duration * percent / 100),
        remaining_work=duration - int(duration * percent / 100),
        percent_complete=percent,
        status=TaskStatus.IN_PROGRESS if percent > 0 else TaskStatus.TODO,
    )


def test_summary_status_in_progress_when_children_partially_complete() -> None:
    thresholds = resolve_status_thresholds({})  # IN_PROGRESS=1, IN_REVIEW=80, DONE=100
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
        status=TaskStatus.TODO,
    )
    children = [
        _make_child("A", date(2024, 1, 1), date(2024, 1, 2), 480, 50.0),
        _make_child("B", date(2024, 1, 3), date(2024, 1, 4), 480, 0.0),
    ]

    apply_summary_rollup(summary, children, DEFAULT_WORK_WEEK, [])
    summary.status = derive_status_from_percent(
        summary.percent_complete, thresholds, current_status=summary.status
    )

    assert summary.percent_complete == 25.0
    assert summary.status == TaskStatus.IN_PROGRESS


def test_summary_status_in_review_when_rolled_up_percent_hits_threshold() -> None:
    thresholds = resolve_status_thresholds({})  # IN_REVIEW=80
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
        status=TaskStatus.IN_PROGRESS,
    )
    children = [
        _make_child("A", date(2024, 1, 1), date(2024, 1, 2), 480, 80.0),
        _make_child("B", date(2024, 1, 3), date(2024, 1, 4), 480, 80.0),
    ]

    apply_summary_rollup(summary, children, DEFAULT_WORK_WEEK, [])
    summary.status = derive_status_from_percent(
        summary.percent_complete, thresholds, current_status=summary.status
    )

    assert summary.percent_complete == 80.0
    assert summary.status == TaskStatus.IN_REVIEW


def test_summary_status_done_when_all_children_complete() -> None:
    thresholds = resolve_status_thresholds({})  # DONE=100
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
        status=TaskStatus.IN_REVIEW,
    )
    children = [
        _make_child("A", date(2024, 1, 1), date(2024, 1, 2), 480, 100.0),
        _make_child("B", date(2024, 1, 3), date(2024, 1, 4), 480, 100.0),
    ]

    apply_summary_rollup(summary, children, DEFAULT_WORK_WEEK, [])
    summary.status = derive_status_from_percent(
        summary.percent_complete, thresholds, current_status=summary.status
    )

    assert summary.percent_complete == 100.0
    assert summary.status == TaskStatus.DONE


def test_summary_status_resets_to_todo_when_children_cleared() -> None:
    thresholds = resolve_status_thresholds({})
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 2),
        duration=480,
        is_summary=True,
        percent_complete=60.0,
        status=TaskStatus.IN_PROGRESS,
    )

    clear_summary_rollup(summary, DEFAULT_WORK_WEEK, [])
    summary.status = derive_status_from_percent(
        0.0, thresholds, current_status=summary.status
    )

    assert summary.percent_complete == 0.0
    assert summary.status == TaskStatus.TODO


def test_summary_status_respects_custom_thresholds() -> None:
    thresholds = resolve_status_thresholds(
        {"status_thresholds": {"IN_PROGRESS": 1, "IN_REVIEW": 60, "DONE": 100}}
    )
    summary = _build_task(
        name="Summary",
        start_date=date(2024, 1, 1),
        finish_date=date(2024, 1, 1),
        duration=0,
        is_summary=True,
        status=TaskStatus.TODO,
    )
    children = [
        _make_child("A", date(2024, 1, 1), date(2024, 1, 2), 480, 60.0),
        _make_child("B", date(2024, 1, 3), date(2024, 1, 4), 480, 60.0),
    ]

    apply_summary_rollup(summary, children, DEFAULT_WORK_WEEK, [])
    summary.status = derive_status_from_percent(
        summary.percent_complete, thresholds, current_status=summary.status
    )

    assert summary.percent_complete == 60.0
    assert summary.status == TaskStatus.IN_REVIEW
