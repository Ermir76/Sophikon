"""
Resource utilization and over-allocation business logic.

Calculates time-phased resource utilization by querying assignments
and comparing allocated units against resource max_units per day.
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.project import Project
from app.models.resource import Resource
from app.models.task import Task
from app.schema.utilization import (
    AssignmentAllocation,
    DailyAllocation,
    OverAllocationItem,
    OverAllocationResponse,
    ProjectUtilizationSummary,
    ResourceUtilizationResponse,
)


async def _get_assignments_in_range(
    db: AsyncSession,
    project: Project,
    start_date: date,
    end_date: date,
    resource_id: UUID | None = None,
) -> list[Assignment]:
    """
    Get all assignments overlapping a date range within a project.

    An assignment overlaps if its date range intersects [start_date, end_date].
    """
    query = (
        select(Assignment)
        .join(Task, Assignment.task_id == Task.id)
        .where(
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
            Assignment.start_date <= end_date,
            Assignment.finish_date >= start_date,
        )
        .options(selectinload(Assignment.task))
    )

    if resource_id:
        query = query.where(Assignment.resource_id == resource_id)

    result = await db.execute(query)
    return list(result.scalars().all())


def _build_daily_allocations(
    assignments: list[Assignment],
    resource: Resource,
    start_date: date,
    end_date: date,
) -> list[DailyAllocation]:
    """
    Build per-day allocation breakdown for a resource.

    For each day in [start_date, end_date], sum the units from
    all assignments that overlap that day.
    """
    # Pre-compute which assignments fall on each day
    day_assignments: dict[date, list[Assignment]] = defaultdict(list)

    for assignment in assignments:
        if assignment.resource_id != resource.id:
            continue

        # Clamp to the requested range
        a_start = max(assignment.start_date, start_date)
        a_end = min(assignment.finish_date, end_date)

        current = a_start
        while current <= a_end:
            day_assignments[current].append(assignment)
            current += timedelta(days=1)

    # Build daily allocations
    max_units = Decimal(str(resource.max_units))
    allocations: list[DailyAllocation] = []

    current = start_date
    while current <= end_date:
        day_asgns = day_assignments.get(current, [])
        allocated = sum(Decimal(str(a.units)) for a in day_asgns)

        allocations.append(
            DailyAllocation(
                date=current,
                allocated_units=allocated,
                max_units=max_units,
                is_over_allocated=allocated > max_units,
                assignments=[
                    AssignmentAllocation(
                        assignment_id=a.id,
                        task_id=a.task_id,
                        task_name=a.task.name,
                        units=Decimal(str(a.units)),
                    )
                    for a in day_asgns
                ],
            )
        )
        current += timedelta(days=1)

    return allocations


async def get_resource_utilization(
    db: AsyncSession,
    project: Project,
    resource: Resource,
    start_date: date,
    end_date: date,
) -> ResourceUtilizationResponse:
    """
    Compute time-phased utilization for a single resource.

    Returns per-day allocation breakdown with over-allocation flags.
    """
    assignments = await _get_assignments_in_range(
        db, project, start_date, end_date, resource_id=resource.id
    )
    daily = _build_daily_allocations(assignments, resource, start_date, end_date)

    allocated_days = [d for d in daily if d.allocated_units > 0]
    peak = max((d.allocated_units for d in daily), default=Decimal("0"))
    avg = (
        sum(d.allocated_units for d in allocated_days) / len(allocated_days)
        if allocated_days
        else Decimal("0")
    )

    return ResourceUtilizationResponse(
        resource_id=resource.id,
        resource_name=resource.name,
        max_units=Decimal(str(resource.max_units)),
        daily_allocations=daily,
        peak_units=peak,
        average_utilization=avg,
    )


async def get_project_utilization_summary(
    db: AsyncSession,
    project: Project,
    start_date: date,
    end_date: date,
) -> ProjectUtilizationSummary:
    """
    Compute utilization summary for all active resources in a project.
    """
    # Get all active resources
    result = await db.execute(
        select(Resource)
        .where(
            Resource.project_id == project.id,
            Resource.is_active == True,  # noqa: E712
        )
        .order_by(Resource.name.asc())
    )
    resources = list(result.scalars().all())

    # Get all assignments in range
    assignments = await _get_assignments_in_range(db, project, start_date, end_date)

    summaries: list[ResourceUtilizationResponse] = []
    for resource in resources:
        daily = _build_daily_allocations(assignments, resource, start_date, end_date)
        allocated_days = [d for d in daily if d.allocated_units > 0]
        peak = max((d.allocated_units for d in daily), default=Decimal("0"))
        avg = (
            sum(d.allocated_units for d in allocated_days) / len(allocated_days)
            if allocated_days
            else Decimal("0")
        )

        summaries.append(
            ResourceUtilizationResponse(
                resource_id=resource.id,
                resource_name=resource.name,
                max_units=Decimal(str(resource.max_units)),
                daily_allocations=daily,
                peak_units=peak,
                average_utilization=avg,
            )
        )

    return ProjectUtilizationSummary(resources=summaries)


async def detect_over_allocations(
    db: AsyncSession,
    project: Project,
    start_date: date,
    end_date: date,
) -> OverAllocationResponse:
    """
    Detect all over-allocated resource+day pairs in a project date range.

    A resource is over-allocated on a day when its total assigned units
    exceed its max_units.
    """
    # Get all active resources
    result = await db.execute(
        select(Resource)
        .where(
            Resource.project_id == project.id,
            Resource.is_active == True,  # noqa: E712
        )
        .order_by(Resource.name.asc())
    )
    resources = list(result.scalars().all())

    # Get all assignments in range
    assignments = await _get_assignments_in_range(db, project, start_date, end_date)

    items: list[OverAllocationItem] = []
    for resource in resources:
        daily = _build_daily_allocations(assignments, resource, start_date, end_date)
        for day in daily:
            if day.is_over_allocated:
                items.append(
                    OverAllocationItem(
                        resource_id=resource.id,
                        resource_name=resource.name,
                        date=day.date,
                        allocated_units=day.allocated_units,
                        max_units=day.max_units,
                        exceeds_by=day.allocated_units - day.max_units,
                    )
                )

    return OverAllocationResponse(items=items, total_count=len(items))
