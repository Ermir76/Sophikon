"""
Insights service for dashboard and project overview control-center endpoints.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ProjectStatus
from app.models.organization import Organization
from app.models.project import Project
from app.models.resource import Resource
from app.models.task import Task
from app.schema.insights import (
    DashboardInsightsResponse,
    DashboardKpis,
    ProjectHealthItem,
    ProjectOverviewInsightsResponse,
    ProjectOverviewKpis,
    ProjectOverviewSchedule,
    ProjectRiskItem,
    RecentActivityItem,
    RiskLevel,
    TrendPoint,
)
from app.service import utilization_service

TODAY_PRESET_DAYS = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
}
MILESTONE_SOON_DAYS = 14
RISK_NEAR_DUE_DAYS = 7
RECENT_ACTIVITY_LIMIT = 20
RISK_ITEMS_LIMIT = 8


def resolve_window(
    window_preset: str,
    start_date: date | None,
    end_date: date | None,
) -> tuple[date, date]:
    """
    Resolve a dashboard window to concrete [start_date, end_date].
    """
    today = date.today()

    if window_preset == "custom":
        if not start_date or not end_date:
            raise ValueError("start_date and end_date are required for custom window")
        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date")
        return start_date, end_date

    if window_preset not in TODAY_PRESET_DAYS:
        raise ValueError("Invalid window preset")

    days = TODAY_PRESET_DAYS[window_preset]
    return today - timedelta(days=days - 1), today


def _to_float(value: object) -> float:
    try:
        return float(value)  # noqa: TRY301
    except Exception:
        return 0.0


def _round2(value: float) -> float:
    return round(value, 2)


def _risk_level(score: float) -> RiskLevel:
    if score >= 67:
        return "high"
    if score >= 34:
        return "medium"
    return "low"


def _build_day_buckets(
    start_date: date,
    end_date: date,
) -> dict[date, TrendPoint]:
    buckets: dict[date, TrendPoint] = {}
    current = start_date
    while current <= end_date:
        buckets[current] = TrendPoint(date=current)
        current += timedelta(days=1)
    return buckets


def _task_completion_metrics(tasks: list[Task], today: date) -> dict[str, float]:
    total = len(tasks)
    completed = sum(1 for t in tasks if _to_float(t.percent_complete) >= 100.0)
    overdue = sum(
        1
        for t in tasks
        if t.finish_date < today and _to_float(t.percent_complete) < 100.0
    )
    critical = sum(1 for t in tasks if bool(t.is_critical))
    completion_pct = (completed / total * 100) if total else 0.0
    return {
        "total": float(total),
        "completed": float(completed),
        "overdue": float(overdue),
        "critical": float(critical),
        "completion_pct": completion_pct,
    }


def _build_trend(
    tasks: list[Task], start_date: date, end_date: date
) -> list[TrendPoint]:
    buckets = _build_day_buckets(start_date, end_date)
    for task in tasks:
        created_day = task.created_at.date()
        if created_day in buckets:
            buckets[created_day].created_tasks += 1

        updated_day = task.updated_at.date()
        if _to_float(task.percent_complete) >= 100.0 and updated_day in buckets:
            buckets[updated_day].completed_tasks += 1

        completion_day: date | None = None
        if _to_float(task.percent_complete) >= 100.0:
            # Best-available approximation: completed timestamp comes from updated_at.
            completion_day = updated_day

        # Overdue starts the day after the planned finish date.
        overdue_day = task.finish_date + timedelta(days=1)
        was_overdue = completion_day is None or completion_day > task.finish_date
        if was_overdue and overdue_day in buckets:
            # Count an overdue "entry event" once on the day the task becomes overdue.
            buckets[overdue_day].overdue_tasks += 1

    return [buckets[d] for d in sorted(buckets)]


def _activity_action(created_at: datetime, updated_at: datetime) -> str:
    # If timestamps are effectively the same, treat as "created", else "updated".
    if abs((updated_at - created_at).total_seconds()) < 1:
        return "created"
    return "updated"


def _build_recent_activity(
    projects: list[Project],
    tasks: list[Task],
    resources: list[Resource],
    project_name_by_id: dict[UUID, str],
) -> list[RecentActivityItem]:
    activities: list[RecentActivityItem] = []

    for p in projects:
        activities.append(
            RecentActivityItem(
                entity_type="project",
                entity_id=p.id,
                entity_name=p.name,
                action=_activity_action(p.created_at, p.updated_at),  # type: ignore[arg-type]
                timestamp=p.updated_at,  # type: ignore[arg-type]
                project_id=p.id,
                project_name=p.name,
            )
        )

    for t in tasks:
        activities.append(
            RecentActivityItem(
                entity_type="task",
                entity_id=t.id,
                entity_name=t.name,
                action=_activity_action(t.created_at, t.updated_at),  # type: ignore[arg-type]
                timestamp=t.updated_at,  # type: ignore[arg-type]
                project_id=t.project_id,
                project_name=project_name_by_id.get(t.project_id),
            )
        )

    for r in resources:
        activities.append(
            RecentActivityItem(
                entity_type="resource",
                entity_id=r.id,
                entity_name=r.name,
                action=_activity_action(r.created_at, r.updated_at),  # type: ignore[arg-type]
                timestamp=r.updated_at,  # type: ignore[arg-type]
                project_id=r.project_id,
                project_name=project_name_by_id.get(r.project_id),
            )
        )

    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:RECENT_ACTIVITY_LIMIT]


async def _project_overallocation_stats(
    db: AsyncSession,
    project: Project,
    start_date: date,
    end_date: date,
) -> tuple[int, float]:
    overalloc = await utilization_service.detect_over_allocations(
        db, project, start_date, end_date
    )
    unique_overallocated = {item.resource_id for item in overalloc.items}

    total_resources_result = await db.execute(
        select(Resource).where(
            Resource.project_id == project.id,
            Resource.is_active == True,  # noqa: E712
        )
    )
    total_resources = len(total_resources_result.scalars().all())

    count = len(unique_overallocated)
    ratio = (count / total_resources) if total_resources else 0.0
    return count, ratio


def _risk_score(
    overdue_ratio: float, critical_ratio: float, overalloc_ratio: float
) -> float:
    score = overdue_ratio * 40 + critical_ratio * 35 + overalloc_ratio * 25
    return _round2(max(0.0, min(100.0, score)))


async def get_org_dashboard_insights(
    db: AsyncSession,
    organization: Organization,
    start_date: date,
    end_date: date,
) -> DashboardInsightsResponse:
    today = date.today()

    projects_result = await db.execute(
        select(Project).where(
            Project.organization_id == organization.id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    projects = list(projects_result.scalars().all())
    project_name_by_id = {p.id: p.name for p in projects}
    project_ids = [p.id for p in projects]

    if not project_ids:
        return DashboardInsightsResponse(
            kpis=DashboardKpis(),
            project_health=[],
            trend=_build_trend([], start_date, end_date),
            recent_activity=[],
        )

    tasks_result = await db.execute(
        select(Task).where(
            Task.project_id.in_(project_ids),
            Task.is_deleted == False,  # noqa: E712
        )
    )
    tasks = list(tasks_result.scalars().all())

    resources_result = await db.execute(
        select(Resource).where(Resource.project_id.in_(project_ids))
    )
    resources = list(resources_result.scalars().all())

    tasks_by_project: dict[UUID, list[Task]] = defaultdict(list)
    for task in tasks:
        tasks_by_project[task.project_id].append(task)

    active_projects = sum(1 for p in projects if p.status == ProjectStatus.ACTIVE)
    completed_projects = sum(1 for p in projects if p.status == ProjectStatus.COMPLETED)

    overall = _task_completion_metrics(tasks, today)

    project_health: list[ProjectHealthItem] = []
    overallocated_resources_total = 0

    # NOTE: Known perf tradeoff. This loop currently performs per-project
    # over-allocation/resource queries (N+1 pattern). If this becomes a
    # bottleneck, batch resource lookups with project_id IN (...) and
    # compute over-allocation in a single pass.
    for project in projects:
        project_tasks = tasks_by_project.get(project.id, [])
        metrics = _task_completion_metrics(project_tasks, today)
        overalloc_count, overalloc_ratio = await _project_overallocation_stats(
            db, project, start_date, end_date
        )
        overallocated_resources_total += overalloc_count

        total_tasks = int(metrics["total"])
        overdue_ratio = float(metrics["overdue"]) / total_tasks if total_tasks else 0.0
        critical_ratio = (
            float(metrics["critical"]) / total_tasks if total_tasks else 0.0
        )
        score = _risk_score(overdue_ratio, critical_ratio, overalloc_ratio)

        project_health.append(
            ProjectHealthItem(
                project_id=project.id,
                name=project.name,
                status=project.status,
                completion_pct=_round2(metrics["completion_pct"]),
                overdue_tasks=int(metrics["overdue"]),
                critical_tasks=int(metrics["critical"]),
                risk_score=score,
                risk_level=_risk_level(score),
            )
        )

    trend = _build_trend(tasks, start_date, end_date)
    recent_activity = _build_recent_activity(
        projects=projects,
        tasks=tasks,
        resources=resources,
        project_name_by_id=project_name_by_id,
    )

    return DashboardInsightsResponse(
        kpis=DashboardKpis(
            active_projects=active_projects,
            completed_projects=completed_projects,
            task_completion_pct=_round2(overall["completion_pct"]),
            overdue_tasks=int(overall["overdue"]),
            critical_tasks=int(overall["critical"]),
            overallocated_resources=overallocated_resources_total,
        ),
        project_health=sorted(project_health, key=lambda x: x.risk_score, reverse=True),
        trend=trend,
        recent_activity=recent_activity,
    )


def _build_project_risk_items(tasks: list[Task], today: date) -> list[ProjectRiskItem]:
    scored_items: list[tuple[float, Task, str]] = []

    for task in tasks:
        percent = _to_float(task.percent_complete)
        overdue = task.finish_date < today and percent < 100.0
        critical = bool(task.is_critical)
        near_due = (
            today <= task.finish_date <= today + timedelta(days=RISK_NEAR_DUE_DAYS)
            and percent < 70.0
        )

        if not (overdue or critical or near_due):
            continue

        if overdue and critical:
            reason = "Overdue + critical path"
        elif overdue:
            reason = "Overdue"
        elif critical:
            reason = "Critical path"
        else:
            reason = "Near due date with low progress"

        score = 0.0
        if overdue:
            score += 50
        if critical:
            score += 30
        if near_due:
            score += 15
        score += max(0.0, (70.0 - percent) * 0.3)

        scored_items.append((score, task, reason))

    scored_items.sort(
        key=lambda x: (x[0], -_to_float(x[1].percent_complete)), reverse=True
    )

    risk_items: list[ProjectRiskItem] = []
    for _, task, reason in scored_items[:RISK_ITEMS_LIMIT]:
        risk_items.append(
            ProjectRiskItem(
                task_id=task.id,
                name=task.name,
                reason=reason,
                finish_date=task.finish_date,
                percent_complete=_round2(_to_float(task.percent_complete)),
                is_critical=bool(task.is_critical),
            )
        )
    return risk_items


async def get_project_overview_insights(
    db: AsyncSession,
    project: Project,
    start_date: date,
    end_date: date,
) -> ProjectOverviewInsightsResponse:
    today = date.today()

    tasks_result = await db.execute(
        select(Task).where(
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    tasks = list(tasks_result.scalars().all())

    resources_result = await db.execute(
        select(Resource).where(
            Resource.project_id == project.id,
            Resource.is_active == True,  # noqa: E712
        )
    )
    active_resources = list(resources_result.scalars().all())

    overview_metrics = _task_completion_metrics(tasks, today)
    overallocated_resources, _ = await _project_overallocation_stats(
        db, project, start_date, end_date
    )

    finish_date = project.finish_date
    if not finish_date and tasks:
        finish_date = max(t.finish_date for t in tasks)

    days_remaining = None
    if finish_date is not None:
        days_remaining = (finish_date - today).days

    milestones_due_soon = sum(
        1
        for t in tasks
        if t.is_milestone
        and today <= t.finish_date <= today + timedelta(days=MILESTONE_SOON_DAYS)
        and _to_float(t.percent_complete) < 100.0
    )

    trend = _build_trend(tasks, start_date, end_date)
    risk_items = _build_project_risk_items(tasks, today)
    recent_activity = _build_recent_activity(
        projects=[project],
        tasks=tasks,
        resources=active_resources,
        project_name_by_id={project.id: project.name},
    )

    return ProjectOverviewInsightsResponse(
        kpis=ProjectOverviewKpis(
            total_tasks=int(overview_metrics["total"]),
            completion_pct=_round2(overview_metrics["completion_pct"]),
            overdue_tasks=int(overview_metrics["overdue"]),
            critical_tasks=int(overview_metrics["critical"]),
            total_resources=len(active_resources),
            overallocated_resources=overallocated_resources,
        ),
        schedule=ProjectOverviewSchedule(
            start_date=project.start_date,
            finish_date=finish_date,
            days_remaining=days_remaining,
            milestones_due_soon=milestones_due_soon,
        ),
        trend=trend,
        risk_items=risk_items,
        recent_activity=recent_activity,
    )
