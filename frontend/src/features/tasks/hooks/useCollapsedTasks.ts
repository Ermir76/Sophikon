import { useMemo, useLayoutEffect, useRef } from "react";
import { useLocalStorageSet } from "@/shared/hooks/useLocalStorageSet";
import type { Task } from "@/features/tasks/types";

/**
 * Manages collapsed task state with localStorage persistence.
 *
 * Handles a key edge case: when indent/outdent changes a task's parent,
 * any collapsed ancestors in the new parent chain are automatically expanded
 * so the task stays visible. Uses useLayoutEffect to prevent visual flicker.
 */
export function useCollapsedTasks(projectId: string, data: Task[]) {
    const { value: collapsedTaskIds, toggle: toggleTaskCollapse, remove: removeCollapsed } = useLocalStorageSet(
        `sophikon:collapsed_tasks:${projectId}`
    );

    // Snapshot of each task's parent_task_id so we can detect hierarchy changes.
    const prevParentsRef = useRef<Map<string, string | undefined>>(
        new Map(data.map(t => [t.id, t.parent_task_id]))
    );

    // When data changes (after indent/outdent/reorder), detect tasks whose
    // parent changed and expand any collapsed ancestors so they stay visible.
    // Runs before paint to prevent flicker.
    useLayoutEffect(() => {
        const dataMap = new Map<string, Task>(data.map(t => [t.id, t]));

        for (const task of data) {
            // Skip tasks not seen before (e.g. collapsed children reappearing
            // after a server refetch replaces an optimistic visible-only cache).
            if (!prevParentsRef.current.has(task.id)) continue;

            const prevParent = prevParentsRef.current.get(task.id);

            if (task.parent_task_id && task.parent_task_id !== prevParent) {
                let ancestor: string | undefined = task.parent_task_id;
                while (ancestor) {
                    if (collapsedTaskIds.has(ancestor)) {
                        removeCollapsed(ancestor);
                    }
                    const parentTask = dataMap.get(ancestor);
                    ancestor = parentTask?.parent_task_id;
                }
            }
        }

        prevParentsRef.current = new Map(data.map(t => [t.id, t.parent_task_id]));
    }, [data, collapsedTaskIds, removeCollapsed]);

    // Filter out tasks whose ancestors are collapsed.
    const visibleData = useMemo(() => {
        if (collapsedTaskIds.size === 0) return data;

        const dataMap = new Map<string, Task>(data.map(t => [t.id, t]));

        return data.filter(task => {
            let current = task.parent_task_id;
            while (current) {
                if (collapsedTaskIds.has(current)) {
                    return false;
                }
                const parentNode = dataMap.get(current);
                current = parentNode?.parent_task_id;
            }
            return true;
        });
    }, [data, collapsedTaskIds]);

    return { visibleData, collapsedTaskIds, toggleTaskCollapse };
}
