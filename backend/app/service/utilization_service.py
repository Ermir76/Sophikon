"""
Resource utilization and over-allocation business logic.

Calculates time-phased resource utilization by querying assignments
and comparing allocated units against resource max_units per day.
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.project import Project
from app.models.resource import Resource
from app.repository import utilization_repo


def _build_daily_allocations(
    assignments: list[Assignment],
    resource: Resource,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
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
    allocations: list[dict[str, Any]] = []

    current = start_date
    while current <= end_date:
        day_asgns = day_assignments.get(current, [])
        allocated = sum((Decimal(str(a.units)) for a in day_asgns), Decimal("0"))

        allocations.append(
            {
                "date": current,
                "allocated_units": allocated,
                "max_units": max_units,
                "is_over_allocated": allocated > max_units,
                "assignments": [
                    {
                        "assignment_id": a.id,
                        "task_id": a.task_id,
                        "task_name": a.task.name,
                        "units": Decimal(str(a.units)),
                    }
                    for a in day_asgns
                ],
            }
        )
        current += timedelta(days=1)

    return allocations


async def get_resource_utilization(
    db: AsyncSession,
    project: Project,
    resource: Resource,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Compute time-phased utilization for a single resource.

    Returns per-day allocation breakdown with over-allocation flags.
    """
    assignments = await utilization_repo.get_assignments_in_range(
        db,
        project_id=project.id,
        start_date=start_date,
        end_date=end_date,
        resource_id=resource.id,
    )
    daily = _build_daily_allocations(assignments, resource, start_date, end_date)

    allocated_days = [d for d in daily if d["allocated_units"] > 0]
    peak = max((d["allocated_units"] for d in daily), default=Decimal("0"))
    avg = (
        sum((d["allocated_units"] for d in allocated_days), Decimal("0"))
        / Decimal(len(allocated_days))
        if allocated_days
        else Decimal("0")
    )

    return {
        "resource_id": resource.id,
        "resource_name": resource.name,
        "max_units": Decimal(str(resource.max_units)),
        "daily_allocations": daily,
        "peak_units": peak,
        "average_utilization": avg,
    }


async def get_project_utilization_summary(
    db: AsyncSession,
    project: Project,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Compute utilization summary for all active resources in a project.
    """
    resources = await utilization_repo.get_active_resources_for_project(
        db,
        project_id=project.id,
    )

    # Get all assignments in range
    assignments = await utilization_repo.get_assignments_in_range(
        db,
        project_id=project.id,
        start_date=start_date,
        end_date=end_date,
    )

    summaries: list[dict[str, Any]] = []
    for resource in resources:
        daily = _build_daily_allocations(assignments, resource, start_date, end_date)
        allocated_days = [d for d in daily if d["allocated_units"] > 0]
        peak = max((d["allocated_units"] for d in daily), default=Decimal("0"))
        avg = (
            sum((d["allocated_units"] for d in allocated_days), Decimal("0"))
            / Decimal(len(allocated_days))
            if allocated_days
            else Decimal("0")
        )

        summaries.append(
            {
                "resource_id": resource.id,
                "resource_name": resource.name,
                "max_units": Decimal(str(resource.max_units)),
                "daily_allocations": daily,
                "peak_units": peak,
                "average_utilization": avg,
            }
        )

    return {"resources": summaries}


async def detect_over_allocations(
    db: AsyncSession,
    project: Project,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Detect all over-allocated resource+day pairs in a project date range.

    A resource is over-allocated on a day when its total assigned units
    exceed its max_units.
    """
    resources = await utilization_repo.get_active_resources_for_project(
        db,
        project_id=project.id,
    )

    # Get all assignments in range
    assignments = await utilization_repo.get_assignments_in_range(
        db,
        project_id=project.id,
        start_date=start_date,
        end_date=end_date,
    )

    items: list[dict[str, Any]] = []
    for resource in resources:
        daily = _build_daily_allocations(assignments, resource, start_date, end_date)
        for day in daily:
            if day["is_over_allocated"]:
                items.append(
                    {
                        "resource_id": resource.id,
                        "resource_name": resource.name,
                        "date": day["date"],
                        "allocated_units": day["allocated_units"],
                        "max_units": day["max_units"],
                        "exceeds_by": day["allocated_units"] - day["max_units"],
                    }
                )

    return {"items": items, "total_count": len(items)}
