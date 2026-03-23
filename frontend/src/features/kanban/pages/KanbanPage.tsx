import { useCallback, useEffect, useMemo } from "react";
import { useParams } from "react-router";
import { toast } from "sonner";
import { useProject, useUpdateProject } from "@/features/projects";
import { TaskDetailPanel, useDependencies, useTasks } from "@/features/tasks";
import { QueryError } from "@/shared/components/QueryError";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { getErrorMessage } from "@/shared/lib/errors";
import { KanbanBoard } from "../components/KanbanBoard";
import { KanbanToolbar, type PriorityFilter } from "../components/KanbanToolbar";
import { useKanbanStore } from "../store/kanban-store";
import {
    KANBAN_COLUMNS,
    type KanbanDependencyIndicatorsByTaskId,
    type KanbanWipLimits,
    type TaskStatus,
} from "../types";
import type { ProjectUpdate } from "@/features/projects";
import type { Task } from "@/features/tasks";

const EMPTY: Task[] = [];

function matchesPriority(priority: number, filter: PriorityFilter): boolean {
    switch (filter) {
        case "high": return priority >= 750;
        case "medium": return priority >= 500 && priority < 750;
        case "low": return priority >= 250 && priority < 500;
        case "minimal": return priority < 250;
        default: return true;
    }
}

function normalizeWipLimits(raw: unknown): KanbanWipLimits {
    if (!raw || typeof raw !== "object") return {};
    const record = raw as Record<string, unknown>;
    const normalized: KanbanWipLimits = {};
    for (const column of KANBAN_COLUMNS) {
        const value = record[column.id];
        if (typeof value === "number" && Number.isInteger(value) && value > 0) {
            normalized[column.id] = value;
        }
    }
    return normalized;
}

function buildProjectSettingsPatch(
    settings: Record<string, unknown> | undefined,
    limits: KanbanWipLimits,
): ProjectUpdate["settings"] {
    return {
        hours_per_day: typeof settings?.hours_per_day === "number" ? settings.hours_per_day : undefined,
        hours_per_week: typeof settings?.hours_per_week === "number" ? settings.hours_per_week : undefined,
        days_per_month: typeof settings?.days_per_month === "number" ? settings.days_per_month : undefined,
        first_day_of_week: typeof settings?.first_day_of_week === "number" ? settings.first_day_of_week : undefined,
        default_task_type:
            settings?.default_task_type === "FIXED_UNITS"
            || settings?.default_task_type === "FIXED_DURATION"
            || settings?.default_task_type === "FIXED_WORK"
                ? settings.default_task_type
                : undefined,
        new_tasks_effort_driven:
            typeof settings?.new_tasks_effort_driven === "boolean"
                ? settings.new_tasks_effort_driven
                : undefined,
        auto_calculate: typeof settings?.auto_calculate === "boolean" ? settings.auto_calculate : undefined,
        kanban_wip_limits: limits,
    };
}

export default function KanbanPage() {
    const { projectId } = useParams<{ projectId: string }>();
    const { data: taskData, isLoading, error, refetch } = useTasks(projectId);
    const { data: dependencyData } = useDependencies(projectId);
    const { data: project } = useProject(projectId);
    const updateProject = useUpdateProject(projectId);

    const searchQuery = useKanbanStore((s) => s.searchQuery);
    const priorityFilter = useKanbanStore((s) => s.priorityFilter);
    const laneModeByProject = useKanbanStore((s) => s.laneModeByProject);
    const selectedTaskId = useKanbanStore((s) => s.selectedTaskId);
    const wipLimitsByProject = useKanbanStore((s) => s.wipLimitsByProject);
    const setSearch = useKanbanStore((s) => s.setSearch);
    const setPriorityFilter = useKanbanStore((s) => s.setPriorityFilter);
    const setProjectLaneMode = useKanbanStore((s) => s.setProjectLaneMode);
    const setSelectedTaskId = useKanbanStore((s) => s.setSelectedTaskId);
    const clearSelectedTaskId = useKanbanStore((s) => s.clearSelectedTaskId);
    const setProjectWipLimits = useKanbanStore((s) => s.setProjectWipLimits);

    const wipLimits = projectId ? (wipLimitsByProject[projectId] ?? {}) : {};
    const laneMode = projectId ? (laneModeByProject[projectId] ?? "none") : "none";

    useEffect(() => {
        if (!projectId || !project) return;
        setProjectWipLimits(
            projectId,
            normalizeWipLimits(project.settings?.kanban_wip_limits),
        );
    }, [projectId, project, setProjectWipLimits]);

    const allTasks = taskData?.items ?? EMPTY;

    const leafTasks = useMemo(() => {
        return allTasks.filter((t) => !t.is_summary);
    }, [allTasks]);

    const filteredLeafTasks = useMemo(() => {
        return leafTasks.filter((t) => {
            if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
            if (!matchesPriority(t.priority, priorityFilter)) return false;
            return true;
        });
    }, [leafTasks, searchQuery, priorityFilter]);

    const dependencyIndicatorsByTaskId = useMemo<KanbanDependencyIndicatorsByTaskId>(() => {
        const indicators: KanbanDependencyIndicatorsByTaskId = {};
        const statusByTaskId: Record<string, TaskStatus> = {};

        for (const task of leafTasks) {
            indicators[task.id] = { blockedCount: 0, blockingCount: 0 };
            statusByTaskId[task.id] = task.status;
        }

        for (const dependency of dependencyData?.items ?? []) {
            if (dependency.is_disabled) continue;

            const predecessorIndicator = indicators[dependency.predecessor_id];
            if (predecessorIndicator) {
                predecessorIndicator.blockingCount += 1;
            }

            const successorIndicator = indicators[dependency.successor_id];
            if (!successorIndicator) continue;

            const predecessorStatus = statusByTaskId[dependency.predecessor_id];
            if (predecessorStatus && predecessorStatus !== "DONE") {
                successorIndicator.blockedCount += 1;
            }
        }

        return indicators;
    }, [leafTasks, dependencyData]);

    const allLeafTasksByStatus = useMemo(() => {
        const map = Object.fromEntries(
            KANBAN_COLUMNS.map((col) => [col.id, [] as Task[]])
        ) as Record<TaskStatus, Task[]>;
        for (const task of leafTasks) {
            (map[task.status] ?? map["BACKLOG"]).push(task);
        }
        return map;
    }, [leafTasks]);

    const tasksByStatus = useMemo(() => {
        const map = Object.fromEntries(
            KANBAN_COLUMNS.map((col) => [col.id, [] as Task[]])
        ) as Record<TaskStatus, Task[]>;
        for (const task of filteredLeafTasks) {
            (map[task.status] ?? map["BACKLOG"]).push(task);
        }
        return map;
    }, [filteredLeafTasks]);

    const handleSetColumnWipLimit = useCallback(async (
        status: TaskStatus,
        limit: number | null,
    ) => {
        if (!projectId || !project) return;

        const previous = wipLimitsByProject[projectId] ?? {};
        const next = { ...previous };
        if (limit === null) {
            delete next[status];
        } else {
            next[status] = limit;
        }

        setProjectWipLimits(projectId, next);

        try {
            await updateProject.mutateAsync({
                settings: buildProjectSettingsPatch(
                    (project.settings ?? {}) as Record<string, unknown>,
                    next,
                ),
            });
        } catch (mutationError) {
            setProjectWipLimits(projectId, previous);
            toast.error(getErrorMessage(mutationError));
        }
    }, [projectId, project, setProjectWipLimits, updateProject, wipLimitsByProject]);

    if (isLoading) return <PageLoading message="Loading tasks..." />;
    if (error) {
        return (
            <div className="p-6">
                <QueryError message="Failed to load tasks." onRetry={() => refetch()} />
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full min-h-0">
            <div className="shrink-0 p-6 pb-4 space-y-4">
                <PageHeader title="Kanban" />
                <KanbanToolbar
                    searchQuery={searchQuery}
                    onSearchChange={setSearch}
                    priorityFilter={priorityFilter}
                    onPriorityFilterChange={setPriorityFilter}
                    laneMode={laneMode}
                    onLaneModeChange={(nextMode) => {
                        if (!projectId) return;
                        setProjectLaneMode(projectId, nextMode);
                    }}
                />
            </div>
            <div className="flex-1 overflow-hidden min-h-0">
                <KanbanBoard
                    tasksByStatus={tasksByStatus}
                    allLeafTasksByStatus={allLeafTasksByStatus}
                    allTasks={allTasks}
                    dependencyIndicatorsByTaskId={dependencyIndicatorsByTaskId}
                    projectId={projectId}
                    wipLimits={wipLimits}
                    laneMode={laneMode}
                    onTaskClick={setSelectedTaskId}
                    onSetColumnWipLimit={handleSetColumnWipLimit}
                />
            </div>
            <TaskDetailPanel
                projectId={projectId ?? ""}
                taskId={selectedTaskId}
                isOpen={!!selectedTaskId}
                onClose={clearSelectedTaskId}
            />
        </div>
    );
}
