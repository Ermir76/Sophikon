"""
Service contracts for calendar and calendar-exception use-cases.
"""

from datetime import date
from typing import TypedDict
from uuid import UUID

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


class WorkBreak(TypedDict):
    start: str
    end: str


class WorkDay(TypedDict):
    start: str
    end: str
    breaks: list[WorkBreak]


class RecurrenceRule(TypedDict, total=False):
    type: str
    month: int
    day: int
    weekday: int
    interval: int


class CalendarCreateInput(TypedDict):
    name: str
    is_base: bool
    work_week: list[WorkDay | None] | None
    base_calendar_id: UUID | None


class CalendarPatchInput(TypedDict, total=False):
    name: str
    is_base: bool
    work_week: list[WorkDay | None] | None
    base_calendar_id: UUID | None


class CalendarExceptionCreateInput(TypedDict):
    name: str
    start_date: date
    end_date: date
    is_working: bool
    work_times: WorkDay | None
    recurrence: RecurrenceRule | None


class CalendarExceptionPatchInput(TypedDict, total=False):
    name: str
    start_date: date
    end_date: date
    is_working: bool
    work_times: WorkDay | None
    recurrence: RecurrenceRule | None
