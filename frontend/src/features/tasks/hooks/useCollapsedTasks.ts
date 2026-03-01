import { useCollapsedTree } from "@/shared/hooks/useCollapsedTree";
import type { Task } from "@/features/tasks/types";

const getParentId = (t: Task) => t.parent_task_id;

/**
 * Collapsed task state for the tasks feature.
 * Thin wrapper around the generic useCollapsedTree hook.
 */
export function useCollapsedTasks(projectId: string, data: Task[]) {
    const { visibleData, collapsedIds: collapsedTaskIds, toggleCollapse: toggleTaskCollapse } =
        useCollapsedTree(`sophikon:collapsed_tasks:${projectId}`, data, getParentId);

    return { visibleData, collapsedTaskIds, toggleTaskCollapse };
}
