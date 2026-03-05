"""Summary rendering for seed runs."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.service import insights_service


async def build_post_seed_summary(
    db: AsyncSession,
    *,
    organization_id: UUID,
    seeded_project_state_by_id: dict[UUID, str],
    start_date: date,
    end_date: date,
) -> list[str]:
    lines: list[str] = []
    organization_result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = organization_result.scalar_one_or_none()
    if organization is None:
        return lines

    dashboard = await insights_service.get_org_dashboard_insights(
        db, organization, start_date, end_date
    )

    lines.append("")
    lines.append("Portfolio KPI snapshot (30d window):")
    lines.append(
        f"  Active={dashboard.kpis.active_projects} "
        f"Completed={dashboard.kpis.completed_projects} "
        f"Completion={dashboard.kpis.task_completion_pct:.1f}% "
        f"Overdue={dashboard.kpis.overdue_tasks} "
        f"Critical={dashboard.kpis.critical_tasks} "
        f"Overallocated={dashboard.kpis.overallocated_resources}"
    )

    if dashboard.project_health:
        lines.append("  Project health:")
        for row in dashboard.project_health:
            state = seeded_project_state_by_id.get(row.project_id, "-")
            lines.append(
                f"    - {row.name}: risk={row.risk_level}({row.risk_score:.1f}) "
                f"completion={row.completion_pct:.1f}% overdue={row.overdue_tasks} "
                f"critical={row.critical_tasks} state={state}"
            )

    return lines
