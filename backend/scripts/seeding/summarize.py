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
    kpis = dashboard.get("kpis", {})
    lines.append(
        f"  Active={kpis.get('active_projects', 0)} "
        f"Completed={kpis.get('completed_projects', 0)} "
        f"Completion={float(kpis.get('task_completion_pct', 0.0)):.1f}% "
        f"Overdue={kpis.get('overdue_tasks', 0)} "
        f"Critical={kpis.get('critical_tasks', 0)} "
        f"Overallocated={kpis.get('overallocated_resources', 0)}"
    )

    project_health = dashboard.get("project_health", [])
    if project_health:
        lines.append("  Project health:")
        for row in project_health:
            project_id = row.get("project_id")
            state = seeded_project_state_by_id.get(project_id, "-")
            lines.append(
                f"    - {row.get('name', '-')}: "
                f"risk={row.get('risk_level', '-')}({float(row.get('risk_score', 0.0)):.1f}) "
                f"completion={float(row.get('completion_pct', 0.0)):.1f}% "
                f"overdue={row.get('overdue_tasks', 0)} "
                f"critical={row.get('critical_tasks', 0)} state={state}"
            )

    return lines
