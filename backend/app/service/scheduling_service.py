"""
Scheduling engine — Critical Path Method (CPM).

Handles forward/backward passes, critical path calculation,
slack/float computation, constraint handling, and summary task rollup.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, timedelta
from math import trunc
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar_exception import CalendarException
from app.models.dependency import Dependency
from app.models.enums import ConstraintType, DependencyType
from app.models.project import Project
from app.models.task import Task
from app.service.calendar_utils import (
    add_working_duration,
    get_working_minutes_on_date,
    next_working_day,
    subtract_working_duration,
    working_minutes_between,
)
from app.service.task_rollup_service import (
    apply_summary_rollup,
    load_effective_calendars,
    load_project_rollup_calendar,
)

# ── Result Dataclass ──


@dataclass
class ScheduleResult:
    """Result of a schedule calculation."""

    project_finish_date: date | None
    critical_path_task_ids: list[UUID]
    tasks_updated: int


@dataclass
class CriticalPathDetails:
    """Resolved details for one ordered driving critical path."""

    task_ids: list[UUID]
    path_length_days: int


# ── Internal data structures ──


@dataclass
class _TaskScheduleData:
    """Intermediate scheduling data for a single task during CPM."""

    task: Task
    es: date  # Early Start
    ef: date  # Early Finish
    ls: date | None = None  # Late Start
    lf: date | None = None  # Late Finish
    total_slack: int = 0
    free_slack: int = 0
    is_critical: bool = False


# ── Calendar Resolution ──


def _get_task_calendar(
    task: Task,
    project_work_week: list[dict | None],
    project_exceptions: list[CalendarException],
    effective_task_calendars: dict[
        UUID, tuple[list[dict | None], list[CalendarException]]
    ],
) -> tuple[list[dict | None], list[CalendarException]]:
    """
    Resolve the effective calendar for a task.

    Precedence:
    1) Task-level calendar override
    2) Project default calendar
    3) System default work week (provided by calendar loader fallback)
    """
    if task.calendar_id and task.calendar_id in effective_task_calendars:
        return effective_task_calendars[task.calendar_id]
    return project_work_week, project_exceptions


# ── Topological Sort ──


def _topological_sort(
    task_ids: list[UUID],
    successors_map: dict[UUID, list[UUID]],
    predecessors_map: dict[UUID, list[UUID]],
) -> list[UUID]:
    """
    Kahn's algorithm for topological sort.

    Returns task IDs in dependency order (predecessors before successors).
    Tasks with no predecessors come first.
    """
    in_degree: dict[UUID, int] = {tid: 0 for tid in task_ids}
    for tid in task_ids:
        in_degree[tid] = len(predecessors_map.get(tid, []))

    queue: deque[UUID] = deque()
    for tid in task_ids:
        if in_degree[tid] == 0:
            queue.append(tid)

    result: list[UUID] = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for succ_id in successors_map.get(node, []):
            if succ_id in in_degree:
                in_degree[succ_id] -= 1
                if in_degree[succ_id] == 0:
                    queue.append(succ_id)

    return result


# ── Dependency Date Calculation ──


def _compute_dep_driven_date(
    dep: Dependency,
    pred_data: _TaskScheduleData,
    succ_duration: int,
    work_week: list[dict | None],
    exceptions: list[CalendarException],
) -> date:
    """
    Compute the earliest start date for a successor driven by a single dependency.

    Handles all four dependency types (FS, SS, FF, SF) and lag.
    """
    daily_minutes = max(
        get_working_minutes_on_date(pred_data.ef, work_week, exceptions),
        1,
    )
    # Convert lag minutes to whole working-day offsets using truncation toward zero.
    # This supports both positive lag and negative lead consistently.
    lag_days = trunc(dep.lag / daily_minutes)
    lag_delta = timedelta(days=lag_days)

    if dep.type == DependencyType.FS:
        # Successor starts after predecessor finishes + lag
        driven = pred_data.ef + timedelta(days=1) + lag_delta
    elif dep.type == DependencyType.SS:
        # Successor starts when predecessor starts + lag
        driven = pred_data.es + lag_delta
    elif dep.type == DependencyType.FF:
        # Successor finishes when predecessor finishes + lag
        # So successor start = pred.EF + lag - successor.duration
        driven_finish = pred_data.ef + lag_delta
        driven = subtract_working_duration(
            driven_finish, succ_duration, work_week, exceptions
        )
    elif dep.type == DependencyType.SF:
        # Predecessor start drives successor finish + lag
        driven_finish = pred_data.es + lag_delta
        driven = subtract_working_duration(
            driven_finish, succ_duration, work_week, exceptions
        )
    else:
        driven = pred_data.ef + timedelta(days=1)

    return next_working_day(driven, work_week, exceptions)


# ── Main Scheduling Function ──


async def calculate_schedule(
    db: AsyncSession,
    project: Project,
) -> ScheduleResult:
    """
    Full CPM schedule calculation for a project.

    1. Load tasks and dependencies
    2. Topological sort
    3. Forward pass (ES/EF)
    4. Backward pass (LS/LF)
    5. Slack and critical path
    6. Summary task rollup
    7. Persist results

    Flushes changes but does NOT commit — the caller must commit.
    """
    # 1. Load data
    tasks_result = await db.execute(
        select(Task).where(
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    all_tasks = list(tasks_result.scalars().all())

    if not all_tasks:
        project.finish_date = project.start_date
        await db.flush()
        return ScheduleResult(
            project_finish_date=project.start_date,
            critical_path_task_ids=[],
            tasks_updated=0,
        )

    deps_result = await db.execute(
        select(Dependency).where(
            Dependency.project_id == project.id,
            Dependency.is_disabled == False,  # noqa: E712
        )
    )
    all_deps = list(deps_result.scalars().all())

    work_week, exceptions = await load_project_rollup_calendar(db, project)
    effective_task_calendars = await load_effective_calendars(
        db,
        {task.calendar_id for task in all_tasks if task.calendar_id is not None},
    )

    # Separate summary and leaf tasks
    task_map: dict[UUID, Task] = {t.id: t for t in all_tasks}
    summary_ids = {t.id for t in all_tasks if t.is_summary}
    leaf_tasks = [t for t in all_tasks if not t.is_summary]
    leaf_ids = {t.id for t in leaf_tasks}

    # Build adjacency maps (only for leaf tasks — summaries are rolled up)
    successors_map: dict[UUID, list[UUID]] = defaultdict(list)
    predecessors_map: dict[UUID, list[UUID]] = defaultdict(list)
    dep_map: dict[tuple[UUID, UUID], Dependency] = {}

    for dep in all_deps:
        # Skip deps involving summary tasks — they get dates from children
        if dep.predecessor_id in summary_ids or dep.successor_id in summary_ids:
            continue
        if dep.predecessor_id not in leaf_ids or dep.successor_id not in leaf_ids:
            continue
        successors_map[dep.predecessor_id].append(dep.successor_id)
        predecessors_map[dep.successor_id].append(dep.predecessor_id)
        dep_map[(dep.predecessor_id, dep.successor_id)] = dep

    # 2. Topological sort (leaf tasks only)
    sorted_ids = _topological_sort(
        [t.id for t in leaf_tasks], successors_map, predecessors_map
    )

    # Handle tasks not in the sorted result (isolated from the dep graph)
    sorted_set = set(sorted_ids)
    for t in leaf_tasks:
        if t.id not in sorted_set:
            sorted_ids.append(t.id)

    # 3. Forward pass
    schedule_data: dict[UUID, _TaskScheduleData] = {}
    project_start = project.start_date

    for tid in sorted_ids:
        task = task_map[tid]
        task_ww, task_exceptions = _get_task_calendar(
            task,
            work_week,
            exceptions,
            effective_task_calendars,
        )

        # Determine Early Start from predecessors
        preds = predecessors_map.get(tid, [])
        if preds:
            es_candidates: list[date] = []
            for pred_id in preds:
                if pred_id not in schedule_data:
                    continue
                dep = dep_map.get((pred_id, tid))
                if not dep:
                    continue
                driven = _compute_dep_driven_date(
                    dep,
                    schedule_data[pred_id],
                    task.duration,
                    task_ww,
                    task_exceptions,
                )
                es_candidates.append(driven)
            es = max(es_candidates) if es_candidates else project_start
        else:
            es = project_start

        # Ensure ES is a working day
        es = next_working_day(es, task_ww, task_exceptions)

        # Apply forward-pass constraints
        es = _apply_forward_constraints(task, es, task_ww, task_exceptions)

        # Compute Early Finish
        ef = add_working_duration(es, task.duration, task_ww, task_exceptions)

        schedule_data[tid] = _TaskScheduleData(task=task, es=es, ef=ef)

    # 4. Backward pass
    # Project finish = max EF across all leaf tasks
    project_finish = max(
        (sd.ef for sd in schedule_data.values()), default=project_start
    )

    for tid in reversed(sorted_ids):
        sd = schedule_data[tid]
        task = sd.task
        task_ww, task_exceptions = _get_task_calendar(
            task,
            work_week,
            exceptions,
            effective_task_calendars,
        )

        # Determine Late Finish from successors
        succs = successors_map.get(tid, [])
        if succs:
            lf_candidates: list[date] = []
            for succ_id in succs:
                if succ_id not in schedule_data:
                    continue
                succ_sd = schedule_data[succ_id]
                # LF = successor LS - 1 day (for FS)
                # More precisely: reverse of forward pass logic
                dep = dep_map.get((tid, succ_id))
                if dep and dep.type == DependencyType.FS:
                    lag_daily_minutes = max(
                        get_working_minutes_on_date(sd.ef, task_ww, task_exceptions), 1
                    )
                    lag_days = trunc(dep.lag / lag_daily_minutes)
                    succ_ls = succ_sd.ls if succ_sd.ls else succ_sd.es
                    lf = succ_ls - timedelta(days=1) - timedelta(days=lag_days)
                else:
                    succ_ls = succ_sd.ls if succ_sd.ls else succ_sd.es
                    lf = succ_ls - timedelta(days=1)
                lf_candidates.append(lf)
            lf = min(lf_candidates) if lf_candidates else project_finish
        else:
            lf = project_finish

        # Apply backward-pass constraints
        lf = _apply_backward_constraints(task, lf)

        ls = subtract_working_duration(lf, task.duration, task_ww, task_exceptions)

        sd.lf = lf
        sd.ls = ls

    # 5. Slack and critical path
    # Handle ALAP constraint: set ES=LS, EF=LF
    for sd in schedule_data.values():
        if sd.task.constraint_type == ConstraintType.ALAP:
            if sd.ls is not None and sd.lf is not None:
                sd.es = sd.ls
                sd.ef = sd.lf

    critical_ids: list[UUID] = []

    for tid in sorted_ids:
        sd = schedule_data[tid]
        task_ww, task_exceptions = _get_task_calendar(
            sd.task,
            work_week,
            exceptions,
            effective_task_calendars,
        )

        # Total slack = LS - ES in working minutes
        if sd.ls is not None:
            if sd.ls > sd.es:
                sd.total_slack = working_minutes_between(
                    sd.es,
                    sd.ls - timedelta(days=1),
                    task_ww,
                    task_exceptions,
                )
            else:
                sd.total_slack = 0
        else:
            sd.total_slack = 0

        # Free slack = min(ES of successors) - EF - 1 day, in working minutes
        succs = successors_map.get(tid, [])
        if succs:
            succ_es_dates = [schedule_data[s].es for s in succs if s in schedule_data]
            if succ_es_dates:
                min_succ_es = min(succ_es_dates)
                free_start = sd.ef + timedelta(days=1)
                free_end = min_succ_es - timedelta(days=1)
                if free_end >= free_start:
                    sd.free_slack = working_minutes_between(
                        free_start,
                        free_end,
                        task_ww,
                        task_exceptions,
                    )
                else:
                    sd.free_slack = 0
            else:
                sd.free_slack = 0
        else:
            sd.free_slack = sd.total_slack

        sd.is_critical = sd.total_slack == 0
        if sd.is_critical:
            critical_ids.append(tid)

    # 6. Persist results for leaf tasks (summary tasks get dates from rollup)
    updated = 0
    for sd in schedule_data.values():
        task = sd.task
        if task.is_summary:
            continue
        task.start_date = sd.es
        task.finish_date = sd.ef
        task.total_slack = sd.total_slack
        task.free_slack = sd.free_slack
        task.is_critical = sd.is_critical
        if task.finish_date < task.start_date:
            raise RuntimeError(
                f"Scheduler produced inverted dates for task {task.id}: "
                f"start={task.start_date}, finish={task.finish_date}"
            )
        updated += 1

    # 7. Summary task rollup
    _rollup_summary_tasks(all_tasks, work_week, exceptions, critical_ids)

    # Update project finish date
    all_finish_dates = [t.finish_date for t in all_tasks if not t.is_deleted]
    project.finish_date = max(all_finish_dates) if all_finish_dates else project_start

    await db.flush()

    return ScheduleResult(
        project_finish_date=project.finish_date,
        critical_path_task_ids=critical_ids,
        tasks_updated=updated,
    )


# ── Constraint Helpers ──


def _apply_forward_constraints(
    task: Task,
    es: date,
    work_week: list[dict | None],
    exceptions: list[CalendarException],
) -> date:
    """Apply constraint adjustments during the forward pass."""
    ct = task.constraint_type
    cd = task.constraint_date

    if ct == ConstraintType.MSO and cd:
        # Must Start On — force exact date
        return cd
    elif ct == ConstraintType.MFO and cd:
        # Must Finish On — derive start from finish
        return subtract_working_duration(cd, task.duration, work_week, exceptions)
    elif ct == ConstraintType.SNET and cd:
        # Start No Earlier Than
        return max(es, cd)
    elif ct == ConstraintType.FNET and cd:
        # Finish No Earlier Than — push start so finish >= constraint
        ef_candidate = add_working_duration(es, task.duration, work_week, exceptions)
        if ef_candidate < cd:
            return subtract_working_duration(cd, task.duration, work_week, exceptions)
        return es

    return es


def _apply_backward_constraints(task: Task, lf: date) -> date:
    """Apply constraint adjustments during the backward pass."""
    ct = task.constraint_type
    cd = task.constraint_date

    if ct == ConstraintType.FNLT and cd:
        # Finish No Later Than
        return min(lf, cd)
    elif ct == ConstraintType.SNLT and cd:
        # Start No Later Than — effectively caps LF
        # LS must be <= cd, so LF = cd + duration equivalent
        # We cap LF here; LS will be computed from LF
        return min(lf, cd)
    elif ct == ConstraintType.MFO and cd:
        # Must Finish On
        return cd

    return lf


# ── Summary Task Rollup ──


def _rollup_summary_tasks(
    all_tasks: list[Task],
    work_week: list[dict | None],
    exceptions: list[CalendarException],
    critical_ids: list[UUID],
) -> None:
    """
    Set summary task dates based on their children.

    Summary tasks inherit:
    - start_date = min(children start_date)
    - finish_date = max(children finish_date)
    - is_critical = True if any child is critical
    - total_slack = 0 if critical, else min(children total_slack)
    """
    # Build parent → children map
    children_map: dict[UUID | None, list[Task]] = defaultdict(list)
    for task in all_tasks:
        if not task.is_deleted:
            children_map[task.parent_task_id].append(task)

    # Process bottom-up: deepest summary tasks first
    summary_tasks = [t for t in all_tasks if t.is_summary and not t.is_deleted]
    summary_tasks.sort(key=lambda t: t.outline_level, reverse=True)

    for summary in summary_tasks:
        children = children_map.get(summary.id, [])
        if not children:
            continue

        apply_summary_rollup(summary, children, work_week, exceptions)
        if summary.is_critical:
            critical_ids.append(summary.id)


async def get_critical_path_tasks(
    db: AsyncSession,
    project: Project,
) -> list[Task]:
    """Return all tasks on the critical path for a project."""
    result = await db.execute(
        select(Task)
        .where(
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
            Task.is_critical == True,  # noqa: E712
        )
        .order_by(Task.sort_order.asc())
    )
    return list(result.scalars().all())


def _path_span_days(start_date: date, finish_date: date) -> int:
    return max(0, (finish_date - start_date).days + 1)


async def get_critical_path_details(
    db: AsyncSession,
    project: Project,
) -> CriticalPathDetails:
    """
    Resolve one ordered critical chain and its exact end-to-end span in days.

    This differs from "all critical tasks": if multiple zero-slack tasks exist,
    this returns one driving chain through the dependency graph.
    """
    tasks_result = await db.execute(
        select(Task).where(
            Task.project_id == project.id,
            Task.is_deleted == False,  # noqa: E712
        )
    )
    all_tasks = list(tasks_result.scalars().all())
    critical_leaf_tasks = [
        task for task in all_tasks if not task.is_summary and bool(task.is_critical)
    ]
    if not critical_leaf_tasks:
        return CriticalPathDetails(task_ids=[], path_length_days=0)

    deps_result = await db.execute(
        select(Dependency).where(
            Dependency.project_id == project.id,
            Dependency.is_disabled == False,  # noqa: E712
        )
    )
    all_deps = list(deps_result.scalars().all())
    work_week, exceptions = await load_project_rollup_calendar(db, project)
    effective_task_calendars = await load_effective_calendars(
        db,
        {
            task.calendar_id
            for task in critical_leaf_tasks
            if task.calendar_id is not None
        },
    )

    task_map = {task.id: task for task in critical_leaf_tasks}
    critical_leaf_ids = set(task_map)
    successors_map: dict[UUID, list[UUID]] = defaultdict(list)
    predecessors_map: dict[UUID, list[UUID]] = defaultdict(list)
    dep_map: dict[tuple[UUID, UUID], Dependency] = {}

    for dep in all_deps:
        if dep.predecessor_id not in critical_leaf_ids:
            continue
        if dep.successor_id not in critical_leaf_ids:
            continue
        successors_map[dep.predecessor_id].append(dep.successor_id)
        predecessors_map[dep.successor_id].append(dep.predecessor_id)
        dep_map[(dep.predecessor_id, dep.successor_id)] = dep

    sorted_ids = _topological_sort(
        [task.id for task in critical_leaf_tasks], successors_map, predecessors_map
    )
    sorted_set = set(sorted_ids)
    for task in critical_leaf_tasks:
        if task.id not in sorted_set:
            sorted_ids.append(task.id)

    schedule_data = {
        task.id: _TaskScheduleData(task=task, es=task.start_date, ef=task.finish_date)
        for task in critical_leaf_tasks
    }
    chain_start_by_task: dict[UUID, date] = {}
    predecessor_choice: dict[UUID, UUID | None] = {}

    for task_id in sorted_ids:
        task = task_map[task_id]
        task_ww, task_exceptions = _get_task_calendar(
            task,
            work_week,
            exceptions,
            effective_task_calendars,
        )
        driving_predecessors: list[UUID] = []

        for predecessor_id in predecessors_map.get(task_id, []):
            dep = dep_map.get((predecessor_id, task_id))
            predecessor_data = schedule_data.get(predecessor_id)
            if not dep or not predecessor_data:
                continue

            driven_start = _compute_dep_driven_date(
                dep,
                predecessor_data,
                task.duration,
                task_ww,
                task_exceptions,
            )
            if driven_start == task.start_date:
                driving_predecessors.append(predecessor_id)

        if driving_predecessors:
            best_predecessor = max(
                driving_predecessors,
                key=lambda predecessor_id: (
                    _path_span_days(
                        chain_start_by_task[predecessor_id], task.finish_date
                    ),
                    -task_map[predecessor_id].sort_order,
                ),
            )
            predecessor_choice[task_id] = best_predecessor
            chain_start_by_task[task_id] = chain_start_by_task[best_predecessor]
        else:
            predecessor_choice[task_id] = None
            chain_start_by_task[task_id] = task.start_date

    terminal_task_id = max(
        sorted_ids,
        key=lambda task_id: (
            _path_span_days(
                chain_start_by_task[task_id], task_map[task_id].finish_date
            ),
            task_map[task_id].finish_date.toordinal(),
            -task_map[task_id].sort_order,
        ),
    )

    ordered_task_ids: list[UUID] = []
    current_task_id: UUID | None = terminal_task_id
    while current_task_id is not None:
        ordered_task_ids.append(current_task_id)
        current_task_id = predecessor_choice[current_task_id]
    ordered_task_ids.reverse()

    first_task = task_map[ordered_task_ids[0]]
    last_task = task_map[ordered_task_ids[-1]]
    return CriticalPathDetails(
        task_ids=ordered_task_ids,
        path_length_days=_path_span_days(first_task.start_date, last_task.finish_date),
    )
