"""Upsert helpers for seed portfolio entities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.dependency import Dependency
from app.models.project import Project
from app.models.resource import Resource
from app.models.task import Task
from app.models.user import User
from app.schema.assignment import AssignmentCreate, AssignmentUpdate
from app.schema.dependency import DependencyCreate, DependencyUpdate
from app.schema.resource import ResourceCreate, ResourceUpdate
from app.schema.task import TaskCreate, TaskUpdate
from app.service.assignment_service import create_assignment, update_assignment
from app.service.dependency_service import create_dependency, update_dependency
from app.service.project_service import create_project, update_project
from app.service.resource_service import create_resource, update_resource
from app.service.task_service import create_task, update_task
from scripts.seeding.scenario_definitions import (
    AssignmentSeedBlueprint,
    DependencySeedBlueprint,
    ProjectSeedBlueprint,
    ResourceSeedBlueprint,
    TaskSeedBlueprint,
)

SEED_GENERATOR = "industry-portfolio"
SEED_CODE_PATTERN = re.compile(r"\[seed_code:([^\]]+)\]")


@dataclass
class SyncCounts:
    created: int = 0
    updated: int = 0


def build_seed_meta(
    seed_key: str, scenario_id: str, state_label: str
) -> dict[str, str]:
    return {
        "generator": SEED_GENERATOR,
        "seed_key": seed_key,
        "scenario_id": scenario_id,
        "state_label": state_label,
    }


def extract_seed_code(notes: str | None) -> str | None:
    if not notes:
        return None
    match = SEED_CODE_PATTERN.search(notes)
    return match.group(1) if match else None


def _merge_project_settings(
    current_settings: dict | None,
    seed_key: str,
    scenario_id: str,
    state_label: str,
    *,
    auto_calculate: bool,
) -> dict:
    merged = dict(current_settings or {})
    merged["auto_calculate"] = auto_calculate
    merged["seed_meta"] = build_seed_meta(seed_key, scenario_id, state_label)
    return merged


def is_seeded_project_for(
    project: Project,
    *,
    seed_key: str,
    scenario_id: str,
) -> bool:
    seed_meta = (project.settings or {}).get("seed_meta", {})
    return (
        seed_meta.get("generator") == SEED_GENERATOR
        and seed_meta.get("seed_key") == seed_key
        and seed_meta.get("scenario_id") == scenario_id
    )


async def upsert_project_for_scenario(
    db: AsyncSession,
    *,
    user: User,
    organization_id: UUID,
    scenario: ProjectSeedBlueprint,
    seed_key: str,
) -> tuple[Project, Literal["created", "updated"]]:
    result = await db.execute(
        select(Project).where(
            Project.organization_id == organization_id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    candidates = list(result.scalars().all())
    existing = next(
        (
            project
            for project in candidates
            if is_seeded_project_for(
                project, seed_key=seed_key, scenario_id=scenario.scenario_id
            )
        ),
        None,
    )

    settings_for_seed = _merge_project_settings(
        existing.settings if existing else {},
        seed_key,
        scenario.scenario_id,
        scenario.state_label,
        auto_calculate=False,
    )

    if not existing:
        create_payload = {
            "organization_id": organization_id,
            "name": scenario.title,
            "description": scenario.description,
            "start_date": scenario.start_date,
            "color": scenario.color,
            "settings": settings_for_seed,
        }
        created = await create_project(
            db,
            user,
            create_payload,
        )
        update_patch = {
            "status": scenario.status,
            "settings": settings_for_seed,
            "color": scenario.color,
        }
        created = await update_project(
            db,
            created,
            update_patch,
        )
        return created, "created"

    update_patch = {
        "name": scenario.title,
        "description": scenario.description,
        "start_date": scenario.start_date,
        "status": scenario.status,
        "color": scenario.color,
        "settings": settings_for_seed,
    }
    updated = await update_project(
        db,
        existing,
        update_patch,
    )
    return updated, "updated"


async def finalize_project_settings(
    db: AsyncSession,
    *,
    project: Project,
    scenario: ProjectSeedBlueprint,
    seed_key: str,
) -> Project:
    final_settings = _merge_project_settings(
        project.settings,
        seed_key,
        scenario.scenario_id,
        scenario.state_label,
        auto_calculate=True,
    )
    update_patch = {
        "name": scenario.title,
        "description": scenario.description,
        "status": scenario.status,
        "color": scenario.color,
        "settings": final_settings,
    }
    return await update_project(
        db,
        project,
        update_patch,
    )


async def sync_resources(
    db: AsyncSession,
    *,
    project: Project,
    resources: list[ResourceSeedBlueprint],
) -> tuple[dict[str, Resource], SyncCounts]:
    result = await db.execute(select(Resource).where(Resource.project_id == project.id))
    existing = list(result.scalars().all())
    by_code = {resource.code: resource for resource in existing if resource.code}

    counts = SyncCounts()
    synced: dict[str, Resource] = {}
    for blueprint in resources:
        existing_resource = by_code.get(blueprint.code)
        if existing_resource:
            update_patch = ResourceUpdate(
                name=blueprint.name,
                type=blueprint.resource_type,
                initials=blueprint.initials,
                email=blueprint.email,
                group_name=blueprint.group_name,
                code=blueprint.code,
                max_units=Decimal(str(blueprint.max_units)),
                standard_rate=Decimal(str(blueprint.standard_rate)),
                is_active=True,
            ).model_dump(mode="python", exclude_unset=True)
            updated = await update_resource(
                db,
                existing_resource,
                update_patch,
            )
            counts.updated += 1
            synced[blueprint.code] = updated
            continue

        create_payload = ResourceCreate(
            name=blueprint.name,
            type=blueprint.resource_type,
            initials=blueprint.initials,
            email=blueprint.email,
            group_name=blueprint.group_name,
            code=blueprint.code,
            max_units=Decimal(str(blueprint.max_units)),
            standard_rate=Decimal(str(blueprint.standard_rate)),
        ).model_dump(mode="python")
        created = await create_resource(
            db,
            project,
            create_payload,
        )
        counts.created += 1
        synced[blueprint.code] = created

    return synced, counts


async def sync_tasks(
    db: AsyncSession,
    *,
    project: Project,
    tasks: list[TaskSeedBlueprint],
) -> tuple[dict[str, Task], SyncCounts]:
    result = await db.execute(
        select(Task).where(
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    existing = list(result.scalars().all())

    by_seed_code: dict[str, Task] = {}
    by_name: dict[str, Task] = {}
    for task in existing:
        seed_code = extract_seed_code(task.notes)
        if seed_code:
            by_seed_code[seed_code] = task
        by_name[task.name] = task

    counts = SyncCounts()
    synced: dict[str, Task] = {}
    ordered = sorted(tasks, key=lambda t: (t.parent_code is not None, t.code))
    for blueprint in ordered:
        existing_task = by_seed_code.get(blueprint.code) or by_name.get(blueprint.name)
        parent_id = synced[blueprint.parent_code].id if blueprint.parent_code else None

        if existing_task:
            update_patch = TaskUpdate(
                name=blueprint.name,
                start_date=blueprint.start_date,
                duration=blueprint.duration_days * 480,
                is_milestone=blueprint.is_milestone,
                priority=blueprint.priority,
                notes=blueprint.notes,
                percent_complete=Decimal(str(blueprint.percent_complete)),
            ).model_dump(mode="python", exclude_unset=True)
            updated = await update_task(
                db,
                existing_task,
                update_patch,
                project=project,
            )
            counts.updated += 1
            synced[blueprint.code] = updated
            continue

        create_payload = TaskCreate(
            name=blueprint.name,
            parent_task_id=parent_id,
            start_date=blueprint.start_date,
            duration=blueprint.duration_days * 480,
            is_milestone=blueprint.is_milestone,
            priority=blueprint.priority,
            notes=blueprint.notes,
        ).model_dump(mode="python")
        created = await create_task(
            db,
            project,
            create_payload,
        )
        if blueprint.percent_complete > 0:
            progress_patch = TaskUpdate(
                percent_complete=Decimal(str(blueprint.percent_complete)),
                notes=blueprint.notes,
            ).model_dump(mode="python", exclude_unset=True)
            created = await update_task(
                db,
                created,
                progress_patch,
                project=project,
            )
        counts.created += 1
        synced[blueprint.code] = created

    return synced, counts


async def sync_dependencies(
    db: AsyncSession,
    *,
    project: Project,
    dependency_blueprints: list[DependencySeedBlueprint],
    tasks_by_code: dict[str, Task],
) -> SyncCounts:
    result = await db.execute(
        select(Dependency).where(Dependency.project_id == project.id)
    )
    existing = list(result.scalars().all())
    existing_map = {(dep.predecessor_id, dep.successor_id): dep for dep in existing}
    seen_pairs = set(existing_map.keys())

    counts = SyncCounts()
    for blueprint in dependency_blueprints:
        predecessor = tasks_by_code.get(blueprint.predecessor_code)
        successor = tasks_by_code.get(blueprint.successor_code)
        if not predecessor or not successor:
            continue

        pair_key = (predecessor.id, successor.id)
        if pair_key in seen_pairs and pair_key not in existing_map:
            continue
        existing_dep = existing_map.get(pair_key)
        if existing_dep:
            if (
                existing_dep.lag != blueprint.lag_minutes
                or existing_dep.type != blueprint.dependency_type
            ):
                update_patch = DependencyUpdate(
                    lag=blueprint.lag_minutes,
                    type=blueprint.dependency_type,
                ).model_dump(mode="python", exclude_unset=True)
                await update_dependency(
                    db,
                    existing_dep,
                    update_patch,
                    project=project,
                )
                counts.updated += 1
                seen_pairs.add(pair_key)
            continue

        if pair_key in seen_pairs:
            continue

        create_payload = DependencyCreate(
            predecessor_id=predecessor.id,
            successor_id=successor.id,
            type=blueprint.dependency_type,
            lag=blueprint.lag_minutes,
        ).model_dump(mode="python")
        await create_dependency(
            db,
            project,
            create_payload,
        )
        counts.created += 1
        seen_pairs.add(pair_key)

    return counts


async def sync_assignments(
    db: AsyncSession,
    *,
    assignment_blueprints: list[AssignmentSeedBlueprint],
    tasks_by_code: dict[str, Task],
    resources_by_code: dict[str, Resource],
) -> SyncCounts:
    task_ids = [task.id for task in tasks_by_code.values()]
    if not task_ids:
        return SyncCounts()

    result = await db.execute(
        select(Assignment)
        .join(Task, Assignment.task_id == Task.id)
        .where(Task.id.in_(task_ids))
    )
    existing = list(result.scalars().all())
    existing_map = {
        (assignment.task_id, assignment.resource_id): assignment
        for assignment in existing
    }

    counts = SyncCounts()
    for blueprint in assignment_blueprints:
        task = tasks_by_code.get(blueprint.task_code)
        resource = resources_by_code.get(blueprint.resource_code)
        if not task or not resource:
            continue
        key = (task.id, resource.id)
        existing_assignment = existing_map.get(key)
        if existing_assignment:
            update_patch = AssignmentUpdate(
                units=Decimal(str(blueprint.units)),
                start_date=blueprint.start_date,
                finish_date=blueprint.finish_date,
                work=blueprint.work_minutes,
                remaining_work=blueprint.work_minutes,
            ).model_dump(mode="python", exclude_unset=True)
            await update_assignment(
                db,
                existing_assignment,
                update_patch,
            )
            counts.updated += 1
            continue

        create_payload = AssignmentCreate(
            resource_id=resource.id,
            units=Decimal(str(blueprint.units)),
            start_date=blueprint.start_date,
            finish_date=blueprint.finish_date,
            work=blueprint.work_minutes,
        ).model_dump(mode="python")
        await create_assignment(
            db,
            task,
            create_payload,
        )
        counts.created += 1

    return counts


async def apply_critical_flags(
    db: AsyncSession,
    *,
    tasks_by_code: dict[str, Task],
    task_blueprints: list[TaskSeedBlueprint],
) -> int:
    blueprint_by_code = {task.code: task for task in task_blueprints}
    updated = 0
    for code, task in tasks_by_code.items():
        expected = blueprint_by_code.get(code)
        if not expected:
            continue
        if task.is_critical != expected.is_critical:
            task.is_critical = expected.is_critical
            updated += 1
    if updated:
        await db.commit()
    return updated
