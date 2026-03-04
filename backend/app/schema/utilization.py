"""
Pydantic schemas for Resource Utilization endpoints.

These are read-only response schemas — utilization is computed from assignments.
"""

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

# ── Response Schemas ──


class AssignmentAllocation(BaseModel):
    """A single assignment's contribution to a day's utilization."""

    assignment_id: uuid.UUID
    task_id: uuid.UUID
    task_name: str
    units: Decimal


class DailyAllocation(BaseModel):
    """Utilization breakdown for a single calendar day."""

    date: date
    allocated_units: Decimal
    max_units: Decimal
    is_over_allocated: bool
    assignments: list[AssignmentAllocation]


class ResourceUtilizationResponse(BaseModel):
    """Time-phased utilization for a single resource."""

    resource_id: uuid.UUID
    resource_name: str
    max_units: Decimal
    daily_allocations: list[DailyAllocation]
    peak_units: Decimal
    average_utilization: Decimal


class ProjectUtilizationSummary(BaseModel):
    """Utilization summary for all resources in a project."""

    resources: list[ResourceUtilizationResponse]


class OverAllocationItem(BaseModel):
    """A single over-allocation occurrence."""

    resource_id: uuid.UUID
    resource_name: str
    date: date
    allocated_units: Decimal
    max_units: Decimal
    exceeds_by: Decimal


class OverAllocationResponse(BaseModel):
    """Over-allocation detection results."""

    items: list[OverAllocationItem]
    total_count: int
