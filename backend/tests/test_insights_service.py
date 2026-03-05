from dataclasses import dataclass
from datetime import date, datetime

from app.service.insights_service import _build_trend


@dataclass
class _TaskStub:
    created_at: datetime
    updated_at: datetime
    finish_date: date
    percent_complete: float


def _point_by_day(points, day: date):
    return next(p for p in points if p.date == day)


def test_build_trend_keeps_late_completion_overdue_event():
    # Finish date in window, completed later -> should still count overdue event.
    task = _TaskStub(
        created_at=datetime(2026, 1, 1, 10, 0, 0),
        updated_at=datetime(2026, 1, 6, 9, 0, 0),  # completion day
        finish_date=date(2026, 1, 4),
        percent_complete=100.0,
    )

    trend = _build_trend([task], date(2026, 1, 1), date(2026, 1, 8))
    overdue_day = date(2026, 1, 5)  # day after finish date

    assert _point_by_day(trend, overdue_day).overdue_tasks == 1
    assert _point_by_day(trend, date(2026, 1, 6)).completed_tasks == 1


def test_build_trend_does_not_mark_on_time_completion_as_overdue():
    # Completed on or before finish date -> no overdue event.
    task = _TaskStub(
        created_at=datetime(2026, 1, 1, 10, 0, 0),
        updated_at=datetime(2026, 1, 4, 9, 0, 0),
        finish_date=date(2026, 1, 4),
        percent_complete=100.0,
    )

    trend = _build_trend([task], date(2026, 1, 1), date(2026, 1, 8))
    overdue_day = date(2026, 1, 5)

    assert _point_by_day(trend, overdue_day).overdue_tasks == 0
