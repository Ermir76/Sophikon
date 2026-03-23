import type { TaskStatus } from "@/features/tasks";

export type { TaskStatus };

export type PriorityFilter = "all" | "high" | "medium" | "low" | "minimal";
export type KanbanLaneMode = "none" | "assignee" | "priority";
export type KanbanWipLimits = Partial<Record<TaskStatus, number>>;
export interface KanbanDependencyIndicator {
    blockedCount: number;
    blockingCount: number;
}

export type KanbanDependencyIndicatorsByTaskId = Record<string, KanbanDependencyIndicator>;

export interface KanbanColumn {
    id: TaskStatus;
    label: string;
    color: string;
}

export interface KanbanLaneModeOption {
    value: KanbanLaneMode;
    label: string;
}

export const KANBAN_LANE_MODE_OPTIONS: KanbanLaneModeOption[] = [
    { value: "none", label: "No swimlanes" },
    { value: "assignee", label: "Swimlanes: assignee" },
    { value: "priority", label: "Swimlanes: priority" },
];

export const KANBAN_COLUMNS: KanbanColumn[] = [
    { id: "BACKLOG", label: "Backlog", color: "text-muted-foreground" },
    { id: "TODO", label: "To Do", color: "text-blue-500" },
    { id: "IN_PROGRESS", label: "In Progress", color: "text-yellow-500" },
    { id: "IN_REVIEW", label: "In Review", color: "text-purple-500" },
    { id: "DONE", label: "Done", color: "text-emerald-500" },
];
