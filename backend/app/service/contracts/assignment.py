"""
Service contracts for assignment use-cases.
"""

from datetime import date
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from app.models.enums import RateTable, WorkContour


class AssignmentCreateInput(TypedDict):
    resource_id: UUID
    units: Decimal
    start_date: date
    finish_date: date
    work: int
    work_contour: WorkContour
    rate_table: RateTable


class AssignmentPatchInput(TypedDict, total=False):
    units: Decimal
    start_date: date
    finish_date: date
    work: int
    actual_work: int
    remaining_work: int
    work_contour: WorkContour
    rate_table: RateTable
    percent_work_complete: Decimal
    is_confirmed: bool
