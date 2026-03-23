import type { TaskStatus } from "@/features/tasks";

export type { TaskStatus };

export type PriorityFilter = "all" | "high" | "medium" | "low" | "minimal";
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

export const KANBAN_COLUMNS: KanbanColumn[] = [
    { id: "BACKLOG", label: "Backlog", color: "text-muted-foreground" },
    { id: "TODO", label: "To Do", color: "text-blue-500" },
    { id: "IN_PROGRESS", label: "In Progress", color: "text-yellow-500" },
    { id: "IN_REVIEW", label: "In Review", color: "text-purple-500" },
    { id: "DONE", label: "Done", color: "text-emerald-500" },
];
