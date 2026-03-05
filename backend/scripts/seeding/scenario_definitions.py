"""Scenario blueprints for industry portfolio seed generation."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from app.models.enums import DependencyType, ProjectStatus, ResourceType

ScenarioPackName = Literal["mixed-industry"]


@dataclass(frozen=True)
class ResourceSeedBlueprint:
    code: str
    name: str
    initials: str
    email: str | None
    group_name: str
    standard_rate: float
    max_units: float
    resource_type: ResourceType = ResourceType.WORK


@dataclass(frozen=True)
class TaskSeedBlueprint:
    code: str
    name: str
    parent_code: str | None
    start_date: date
    duration_days: int
    percent_complete: int
    is_critical: bool
    is_milestone: bool
    priority: int
    notes: str | None


@dataclass(frozen=True)
class DependencySeedBlueprint:
    predecessor_code: str
    successor_code: str
    dependency_type: DependencyType
    lag_minutes: int = 0


@dataclass(frozen=True)
class AssignmentSeedBlueprint:
    task_code: str
    resource_code: str
    units: float
    start_date: date
    finish_date: date
    work_minutes: int


@dataclass(frozen=True)
class ProjectSeedBlueprint:
    scenario_id: str
    title: str
    industry: str
    state_label: str
    status: ProjectStatus
    color: str | None
    description: str
    start_date: date
    resources: list[ResourceSeedBlueprint]
    tasks: list[TaskSeedBlueprint]
    dependencies: list[DependencySeedBlueprint]
    assignments: list[AssignmentSeedBlueprint]


@dataclass(frozen=True)
class _PhaseSpec:
    title: str
    task_count: int


_SCENARIO_COLORS = {
    "construction-plant-expansion": "#C97356",
    "manufacturing-line-retrofit": "#C28A2E",
    "pharma-validation-rollout": "#8A77D2",
    "energy-substation-program": "#2F9B87",
    "industrial-commissioning-window": "#3D8CD0",
}


def get_scenario_pack(
    pack: ScenarioPackName,
    *,
    base_date: date,
) -> list[ProjectSeedBlueprint]:
    if pack != "mixed-industry":
        raise ValueError(f"Unsupported scenario pack: {pack}")
    return _build_mixed_industry_pack(base_date)


def _build_mixed_industry_pack(base_date: date) -> list[ProjectSeedBlueprint]:
    return [
        _build_project(
            scenario_id="construction-plant-expansion",
            title="Construction: Plant Expansion",
            industry="Construction",
            state_label="at-risk",
            status=ProjectStatus.ACTIVE,
            description=(
                "Civil and mechanical expansion program with procurement pressure, "
                "critical-path slippage, and coordination risk across work fronts."
            ),
            base_date=base_date,
            start_offset_days=-48,
            strategy="at-risk",
            phase_specs=[
                _PhaseSpec("Site Preparation", 8),
                _PhaseSpec("Foundation and Structural", 8),
                _PhaseSpec("Mechanical Installation", 10),
                _PhaseSpec("Electrical and Controls", 12),
                _PhaseSpec("Commissioning", 12),
            ],
            resource_names=[
                "Construction Manager",
                "Site Engineer",
                "Civil Crew A",
                "Civil Crew B",
                "Steel Team",
                "Mechanical Supervisor",
                "Pipefitting Crew",
                "Electrical Lead",
                "Controls Engineer",
                "QA/QC Inspector",
                "Safety Officer",
                "Planner",
            ],
        ),
        _build_project(
            scenario_id="manufacturing-line-retrofit",
            title="Manufacturing: Line Automation Retrofit",
            industry="Manufacturing",
            state_label="overallocated",
            status=ProjectStatus.ACTIVE,
            description=(
                "Automation retrofit for a legacy production line with heavy overlap "
                "in installation and testing resources."
            ),
            base_date=base_date,
            start_offset_days=-24,
            strategy="overallocated",
            phase_specs=[
                _PhaseSpec("Current-State Assessment", 7),
                _PhaseSpec("Design and Procurement", 8),
                _PhaseSpec("PLC and HMI Development", 9),
                _PhaseSpec("Installation and Cutover", 10),
                _PhaseSpec("Ramp-Up and Stabilization", 11),
            ],
            resource_names=[
                "Program Manager",
                "Industrial Engineer",
                "Automation Engineer",
                "PLC Specialist",
                "Electrical Technician",
                "Mechanical Technician",
                "Commissioning Engineer",
                "Operations Trainer",
                "Quality Engineer",
                "Maintenance Planner",
            ],
        ),
        _build_project(
            scenario_id="pharma-validation-rollout",
            title="Pharma: Validation & Compliance Rollout",
            industry="Pharmaceutical",
            state_label="delayed-recovery",
            status=ProjectStatus.ACTIVE,
            description=(
                "Validation-driven rollout with documentation backlog; some work was "
                "completed late while selected packages remain overdue."
            ),
            base_date=base_date,
            start_offset_days=-42,
            strategy="delayed-recovery",
            phase_specs=[
                _PhaseSpec("URS and Scope Definition", 8),
                _PhaseSpec("DQ and Risk Assessment", 8),
                _PhaseSpec("IQ Preparation", 8),
                _PhaseSpec("OQ and Protocol Execution", 8),
                _PhaseSpec("PQ and Release", 8),
            ],
            resource_names=[
                "Validation Lead",
                "QA Compliance",
                "CSV Engineer",
                "Process Engineer",
                "Manufacturing Rep",
                "Documentation Specialist",
                "Test Coordinator",
                "Regulatory Affairs",
                "Project Controller",
            ],
        ),
        _build_project(
            scenario_id="energy-substation-program",
            title="Energy: Substation Maintenance Program",
            industry="Energy",
            state_label="healthy",
            status=ProjectStatus.ACTIVE,
            description=(
                "Preventive and corrective maintenance package with balanced resource "
                "loading and strong execution cadence."
            ),
            base_date=base_date,
            start_offset_days=-12,
            strategy="healthy",
            phase_specs=[
                _PhaseSpec("Inspection Planning", 7),
                _PhaseSpec("Transformer Service", 7),
                _PhaseSpec("Protection Relay Work", 7),
                _PhaseSpec("Switchyard Activities", 7),
                _PhaseSpec("Closeout and Reporting", 7),
            ],
            resource_names=[
                "Maintenance Manager",
                "Electrical Supervisor",
                "Relay Technician",
                "HV Specialist",
                "Field Operator",
                "Safety Coordinator",
                "Planner Scheduler",
                "Reporting Analyst",
            ],
        ),
        _build_project(
            scenario_id="industrial-commissioning-window",
            title="Industrial Event: Commissioning Window",
            industry="Industrial Operations",
            state_label="near-complete",
            status=ProjectStatus.ACTIVE,
            description=(
                "Short-window commissioning campaign with most packages closed and "
                "a focused tail of final punch-list work."
            ),
            base_date=base_date,
            start_offset_days=-32,
            strategy="near-complete",
            phase_specs=[
                _PhaseSpec("Pre-Commissioning", 6),
                _PhaseSpec("Mechanical Completion", 6),
                _PhaseSpec("Cold Commissioning", 6),
                _PhaseSpec("Hot Commissioning", 6),
                _PhaseSpec("Punch List and Handover", 6),
            ],
            resource_names=[
                "Commissioning Manager",
                "Mechanical Lead",
                "Electrical Lead",
                "Instrumentation Engineer",
                "Operations Liaison",
                "QA Turnover",
                "Shift Coordinator",
                "Handover Controller",
            ],
        ),
    ]


def _build_project(
    *,
    scenario_id: str,
    title: str,
    industry: str,
    state_label: str,
    status: ProjectStatus,
    description: str,
    base_date: date,
    start_offset_days: int,
    strategy: str,
    phase_specs: list[_PhaseSpec],
    resource_names: list[str],
) -> ProjectSeedBlueprint:
    project_start = base_date + timedelta(days=start_offset_days)
    resources = _build_resources(scenario_id, resource_names)
    tasks = _build_tasks(scenario_id, phase_specs, project_start, base_date, strategy)
    dependencies = _build_dependencies(tasks)
    assignments = _build_assignments(
        scenario_id=scenario_id,
        tasks=tasks,
        resources=resources,
        strategy=strategy,
    )

    return ProjectSeedBlueprint(
        scenario_id=scenario_id,
        title=title,
        industry=industry,
        state_label=state_label,
        status=status,
        color=_SCENARIO_COLORS.get(scenario_id),
        description=description,
        start_date=project_start,
        resources=resources,
        tasks=tasks,
        dependencies=dependencies,
        assignments=assignments,
    )


def _build_resources(
    scenario_id: str,
    resource_names: list[str],
) -> list[ResourceSeedBlueprint]:
    resources: list[ResourceSeedBlueprint] = []
    for idx, name in enumerate(resource_names, start=1):
        initials = "".join(part[0] for part in name.split() if part)[:3].upper()
        code = f"{scenario_id}:R{idx:02d}"
        email = f"{scenario_id.replace('-', '.')}.{idx:02d}@example.com"
        resources.append(
            ResourceSeedBlueprint(
                code=code,
                name=name,
                initials=initials,
                email=email,
                group_name="Operations",
                standard_rate=42 + (idx % 6) * 8,
                max_units=1.0,
            )
        )
    return resources


def _build_tasks(
    scenario_id: str,
    phase_specs: list[_PhaseSpec],
    project_start: date,
    base_date: date,
    strategy: str,
) -> list[TaskSeedBlueprint]:
    tasks: list[TaskSeedBlueprint] = []

    for phase_index, phase in enumerate(phase_specs, start=1):
        phase_code = f"{scenario_id}:PH{phase_index:02d}"
        phase_start = project_start + timedelta(days=(phase_index - 1) * 10)
        summary_name = f"{phase.title}"
        tasks.append(
            TaskSeedBlueprint(
                code=phase_code,
                name=summary_name,
                parent_code=None,
                start_date=phase_start,
                duration_days=max(2, phase.task_count),
                percent_complete=0,
                is_critical=False,
                is_milestone=False,
                priority=750,
                notes=_task_notes(phase_code, "summary"),
            )
        )

        for task_index in range(phase.task_count):
            child_code = f"{phase_code}:T{task_index + 1:02d}"
            child_start = phase_start + timedelta(days=task_index * 2)
            duration_days = 2 + ((phase_index + task_index) % 3)
            finish_date = child_start + timedelta(days=duration_days)
            progress, critical = _progress_and_critical(
                strategy=strategy,
                phase_index=phase_index,
                task_index=task_index,
                finish_date=finish_date,
                base_date=base_date,
            )
            is_milestone = task_index == phase.task_count - 1 and (phase_index % 2 == 0)
            if is_milestone:
                duration_days = 0

            tasks.append(
                TaskSeedBlueprint(
                    code=child_code,
                    name=f"{phase.title} - Work Package {task_index + 1:02d}",
                    parent_code=phase_code,
                    start_date=child_start,
                    duration_days=duration_days,
                    percent_complete=progress,
                    is_critical=critical,
                    is_milestone=is_milestone,
                    priority=900 if critical else 550,
                    notes=_task_notes(child_code, strategy),
                )
            )

    return tasks


def _progress_and_critical(
    *,
    strategy: str,
    phase_index: int,
    task_index: int,
    finish_date: date,
    base_date: date,
) -> tuple[int, bool]:
    key = (phase_index * 17 + task_index * 13) % 100
    is_past_due = finish_date < base_date

    if strategy == "healthy":
        if is_past_due:
            return 100, False
        return 70 + (key % 26), key % 19 == 0

    if strategy == "near-complete":
        if phase_index <= 4 or is_past_due:
            return 100 if key % 9 else 90, key % 31 == 0
        return 68 + (key % 25), key % 23 == 0

    if strategy == "at-risk":
        if is_past_due and key % 3 != 0:
            return 25 + (key % 45), True
        if is_past_due:
            return 100, False
        return 35 + (key % 50), key % 4 == 0

    if strategy == "delayed-recovery":
        if is_past_due and key % 4 == 0:
            # Completed late: done now, but due date is in the past.
            return 100, False
        if is_past_due:
            return 30 + (key % 45), key % 2 == 0
        return 45 + (key % 45), key % 6 == 0

    if strategy == "overallocated":
        if is_past_due and key % 5 == 0:
            return 100, False
        if is_past_due:
            return 40 + (key % 40), key % 3 == 0
        return 48 + (key % 38), key % 7 == 0

    return 60, False


def _build_dependencies(
    tasks: list[TaskSeedBlueprint],
) -> list[DependencySeedBlueprint]:
    dependencies: list[DependencySeedBlueprint] = []

    phase_children: dict[str, list[TaskSeedBlueprint]] = {}
    summaries: list[TaskSeedBlueprint] = []
    for task in tasks:
        if task.parent_code is None:
            summaries.append(task)
            phase_children[task.code] = []
        else:
            phase_children.setdefault(task.parent_code, []).append(task)

    ordered_summaries = sorted(summaries, key=lambda t: t.code)
    for summary in ordered_summaries:
        children = sorted(phase_children.get(summary.code, []), key=lambda t: t.code)
        for idx in range(len(children) - 1):
            dependencies.append(
                DependencySeedBlueprint(
                    predecessor_code=children[idx].code,
                    successor_code=children[idx + 1].code,
                    dependency_type=DependencyType.FS,
                )
            )
            if idx % 4 == 0:
                dependencies.append(
                    DependencySeedBlueprint(
                        predecessor_code=children[idx].code,
                        successor_code=children[idx + 1].code,
                        dependency_type=DependencyType.SS,
                    )
                )

    for idx in range(len(ordered_summaries) - 1):
        current_children = sorted(
            phase_children.get(ordered_summaries[idx].code, []),
            key=lambda t: t.code,
        )
        next_children = sorted(
            phase_children.get(ordered_summaries[idx + 1].code, []),
            key=lambda t: t.code,
        )
        if current_children and next_children:
            dependencies.append(
                DependencySeedBlueprint(
                    predecessor_code=current_children[-1].code,
                    successor_code=next_children[0].code,
                    dependency_type=DependencyType.FS,
                )
            )

    return dependencies


def _build_assignments(
    *,
    scenario_id: str,
    tasks: list[TaskSeedBlueprint],
    resources: list[ResourceSeedBlueprint],
    strategy: str,
) -> list[AssignmentSeedBlueprint]:
    assignments: list[AssignmentSeedBlueprint] = []
    leaf_tasks = [task for task in tasks if task.parent_code is not None]

    hotspot_resource = resources[0].code if resources else None
    for idx, task in enumerate(leaf_tasks):
        resource = resources[idx % len(resources)]
        units = 0.75 + ((idx + 3) % 3) * 0.1

        if strategy == "overallocated" and hotspot_resource and idx < 14:
            resource = next(r for r in resources if r.code == hotspot_resource)
            units = 1.2 if idx % 2 == 0 else 1.0
        elif strategy == "healthy":
            units = 0.65 + (idx % 2) * 0.1
        elif strategy == "near-complete":
            units = 0.6 if idx % 5 else 0.8

        duration_days = max(1, task.duration_days)
        finish_date = task.start_date + timedelta(days=duration_days)
        work_minutes = int(duration_days * 480 * units)
        assignments.append(
            AssignmentSeedBlueprint(
                task_code=task.code,
                resource_code=resource.code,
                units=round(units, 2),
                start_date=task.start_date,
                finish_date=finish_date,
                work_minutes=work_minutes,
            )
        )

    return assignments


def _task_notes(code: str, strategy: str) -> str:
    return f"[seed_code:{code}] [seed_profile:{strategy}]"
