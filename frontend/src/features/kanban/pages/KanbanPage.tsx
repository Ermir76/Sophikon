import { useMemo } from "react";
import { useParams } from "react-router";
import { useTasks } from "@/features/tasks";
import { QueryError } from "@/shared/components/QueryError";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { KanbanBoard } from "../components/KanbanBoard";
import { KanbanToolbar, type PriorityFilter } from "../components/KanbanToolbar";
import { useKanbanStore } from "../store/kanban-store";
import { KANBAN_COLUMNS, type TaskStatus } from "../types";
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

export default function KanbanPage() {
    const { projectId } = useParams<{ projectId: string }>();
    const { data: taskData, isLoading, error, refetch } = useTasks(projectId);

    const { searchQuery, priorityFilter, setSearch, setPriorityFilter } = useKanbanStore();

    const filteredLeafTasks = useMemo(() => {
        return (taskData?.items ?? EMPTY).filter((t) => {
            if (t.is_summary) return false;
            if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
            if (!matchesPriority(t.priority, priorityFilter)) return false;
            return true;
        });
    }, [taskData, searchQuery, priorityFilter]);

    const tasksByStatus = useMemo(() => {
        const map = Object.fromEntries(
            KANBAN_COLUMNS.map((col) => [col.id, [] as Task[]])
        ) as Record<TaskStatus, Task[]>;
        for (const task of filteredLeafTasks) {
            (map[task.status] ?? map["BACKLOG"]).push(task);
        }
        return map;
    }, [filteredLeafTasks]);

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
                />
            </div>
            <div className="flex-1 overflow-hidden min-h-0">
                <KanbanBoard tasksByStatus={tasksByStatus} projectId={projectId} />
            </div>
        </div>
    );
}
