"""Seed orchestration for the five-project industry portfolio."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.user import User
from app.service import insights_service, scheduling_service
from app.service.auth_service import get_user_by_email
from app.service.organization_service import list_organizations
from scripts.seeding.scenario_definitions import (
    ProjectSeedBlueprint,
    ScenarioPackName,
    get_scenario_pack,
)
from scripts.seeding.summarize import build_post_seed_summary
from scripts.seeding.upsert import (
    SyncCounts,
    apply_critical_flags,
    finalize_project_settings,
    sync_assignments,
    sync_dependencies,
    sync_resources,
    sync_tasks,
    upsert_project_for_scenario,
)


@dataclass
class ScenarioRunSummary:
    scenario_id: str
    title: str
    state_label: str
    project_id: UUID | None = None
    project_action: str = "planned"
    resources: SyncCounts = field(default_factory=SyncCounts)
    tasks: SyncCounts = field(default_factory=SyncCounts)
    dependencies: SyncCounts = field(default_factory=SyncCounts)
    assignments: SyncCounts = field(default_factory=SyncCounts)
    critical_flags_updated: int = 0
    scheduled_tasks_updated: int = 0
    error: str | None = None


@dataclass
class SeedRunResult:
    dry_run: bool
    user_email: str
    organization_id: UUID
    organization_name: str
    scenario_pack: ScenarioPackName
    seed_key: str
    base_date: date
    scenario_runs: list[ScenarioRunSummary]
    post_seed_lines: list[str] = field(default_factory=list)

    @property
    def totals(self) -> dict[str, int]:
        out = {
            "projects_created": 0,
            "projects_updated": 0,
            "resources_created": 0,
            "resources_updated": 0,
            "tasks_created": 0,
            "tasks_updated": 0,
            "dependencies_created": 0,
            "dependencies_updated": 0,
            "assignments_created": 0,
            "assignments_updated": 0,
            "critical_flags_updated": 0,
            "scheduled_tasks_updated": 0,
            "scenario_errors": 0,
        }
        for item in self.scenario_runs:
            if item.project_action == "created":
                out["projects_created"] += 1
            elif item.project_action == "updated":
                out["projects_updated"] += 1

            out["resources_created"] += item.resources.created
            out["resources_updated"] += item.resources.updated
            out["tasks_created"] += item.tasks.created
            out["tasks_updated"] += item.tasks.updated
            out["dependencies_created"] += item.dependencies.created
            out["dependencies_updated"] += item.dependencies.updated
            out["assignments_created"] += item.assignments.created
            out["assignments_updated"] += item.assignments.updated
            out["critical_flags_updated"] += item.critical_flags_updated
            out["scheduled_tasks_updated"] += item.scheduled_tasks_updated
            if item.error:
                out["scenario_errors"] += 1
        return out


async def seed_industry_portfolio(
    db: AsyncSession,
    *,
    user_email: str,
    org_id: UUID | None = None,
    scenario_pack: ScenarioPackName = "mixed-industry",
    seed_key: str = "v1",
    base_date: date | None = None,
    dry_run: bool = False,
) -> SeedRunResult:
    resolved_base_date = base_date or date.today()
    user = await _resolve_user(db, user_email)
    organization = await _resolve_organization(db, user, org_id=org_id)
    organization_id = organization.id
    organization_name = organization.name
    scenarios = get_scenario_pack(scenario_pack, base_date=resolved_base_date)

    scenario_runs: list[ScenarioRunSummary] = []
    seeded_project_state_by_id: dict[UUID, str] = {}

    if dry_run:
        for scenario in scenarios:
            scenario_runs.append(_dry_run_summary(scenario))
        return SeedRunResult(
            dry_run=True,
            user_email=user_email,
            organization_id=organization_id,
            organization_name=organization_name,
            scenario_pack=scenario_pack,
            seed_key=seed_key,
            base_date=resolved_base_date,
            scenario_runs=scenario_runs,
        )

    for scenario in scenarios:
        summary = ScenarioRunSummary(
            scenario_id=scenario.scenario_id,
            title=scenario.title,
            state_label=scenario.state_label,
        )
        try:
            scenario_user = await _resolve_user(db, user_email)
            project, action = await upsert_project_for_scenario(
                db,
                user=scenario_user,
                organization_id=organization_id,
                scenario=scenario,
                seed_key=seed_key,
            )
            summary.project_id = project.id
            summary.project_action = action

            resources_by_code, summary.resources = await sync_resources(
                db,
                project=project,
                resources=scenario.resources,
            )
            tasks_by_code, summary.tasks = await sync_tasks(
                db,
                project=project,
                tasks=scenario.tasks,
            )
            summary.dependencies = await sync_dependencies(
                db,
                project=project,
                dependency_blueprints=scenario.dependencies,
                tasks_by_code=tasks_by_code,
            )
            summary.assignments = await sync_assignments(
                db,
                assignment_blueprints=scenario.assignments,
                tasks_by_code=tasks_by_code,
                resources_by_code=resources_by_code,
            )
            schedule_result = await scheduling_service.calculate_schedule(db, project)
            await db.commit()
            summary.scheduled_tasks_updated = schedule_result.tasks_updated

            summary.critical_flags_updated = await apply_critical_flags(
                db,
                tasks_by_code=tasks_by_code,
                task_blueprints=scenario.tasks,
            )

            project = await finalize_project_settings(
                db,
                project=project,
                scenario=scenario,
                seed_key=seed_key,
            )
            if summary.project_id:
                seeded_project_state_by_id[summary.project_id] = scenario.state_label
        except Exception as exc:  # noqa: BLE001
            await db.rollback()
            summary.error = str(exc)
        scenario_runs.append(summary)

    window_start, window_end = insights_service.resolve_window("30d", None, None)
    post_seed_lines = (
        await build_post_seed_summary(
            db,
            organization_id=organization_id,
            seeded_project_state_by_id=seeded_project_state_by_id,
            start_date=window_start,
            end_date=window_end,
        )
        if seeded_project_state_by_id
        else []
    )

    return SeedRunResult(
        dry_run=False,
        user_email=user_email,
        organization_id=organization_id,
        organization_name=organization_name,
        scenario_pack=scenario_pack,
        seed_key=seed_key,
        base_date=resolved_base_date,
        scenario_runs=scenario_runs,
        post_seed_lines=post_seed_lines,
    )


def render_seed_result(result: SeedRunResult) -> str:
    lines: list[str] = []
    mode = "DRY RUN" if result.dry_run else "APPLIED"
    lines.append(
        f"[{mode}] Seed pack={result.scenario_pack} key={result.seed_key} "
        f"base_date={result.base_date.isoformat()} "
        f"org={result.organization_name} ({result.organization_id})"
    )
    lines.append(f"User: {result.user_email}")
    lines.append("")
    lines.append("Scenario results:")
    for item in result.scenario_runs:
        base = f"  - {item.title} ({item.state_label}) action={item.project_action}"
        if item.project_id:
            base += f" project_id={item.project_id}"
        if item.error:
            base += f" ERROR={item.error}"
        lines.append(base)
        lines.append(
            "      "
            f"resources c/u={item.resources.created}/{item.resources.updated}, "
            f"tasks c/u={item.tasks.created}/{item.tasks.updated}, "
            f"deps c/u={item.dependencies.created}/{item.dependencies.updated}, "
            f"assignments c/u={item.assignments.created}/{item.assignments.updated}, "
            f"critical_updates={item.critical_flags_updated}, "
            f"scheduled_updates={item.scheduled_tasks_updated}"
        )

    totals = result.totals
    lines.append("")
    lines.append(
        "Totals: "
        f"projects c/u={totals['projects_created']}/{totals['projects_updated']}, "
        f"resources c/u={totals['resources_created']}/{totals['resources_updated']}, "
        f"tasks c/u={totals['tasks_created']}/{totals['tasks_updated']}, "
        f"deps c/u={totals['dependencies_created']}/{totals['dependencies_updated']}, "
        f"assignments c/u={totals['assignments_created']}/{totals['assignments_updated']}, "
        f"critical_updates={totals['critical_flags_updated']}, "
        f"scheduled_updates={totals['scheduled_tasks_updated']}, "
        f"errors={totals['scenario_errors']}"
    )
    lines.extend(result.post_seed_lines)
    return "\n".join(lines)


def _dry_run_summary(scenario: ProjectSeedBlueprint) -> ScenarioRunSummary:
    return ScenarioRunSummary(
        scenario_id=scenario.scenario_id,
        title=scenario.title,
        state_label=scenario.state_label,
        project_action="planned",
        resources=SyncCounts(created=len(scenario.resources), updated=0),
        tasks=SyncCounts(created=len(scenario.tasks), updated=0),
        dependencies=SyncCounts(created=len(scenario.dependencies), updated=0),
        assignments=SyncCounts(created=len(scenario.assignments), updated=0),
    )


async def _resolve_user(db: AsyncSession, user_email: str) -> User:
    user = await get_user_by_email(db, user_email)
    if not user:
        raise ValueError(f"User not found: {user_email}")
    return user


async def _resolve_organization(
    db: AsyncSession,
    user: User,
    *,
    org_id: UUID | None,
) -> Organization:
    organizations, _ = await list_organizations(db, user, page=1, per_page=100)
    if not organizations:
        raise ValueError("No organizations found for user")
    if org_id is None:
        return organizations[0]

    matched = next((org for org in organizations if org.id == org_id), None)
    if not matched:
        raise ValueError(f"Organization {org_id} not found in user's memberships")
    return matched
