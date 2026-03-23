import { useState, useCallback } from "react";
import { useSensors, useSensor, PointerSensor } from "@dnd-kit/core";
import type { DragStartEvent, DragEndEvent } from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import { toast } from "sonner";
import { useReorderTask, useUpdateTask } from "@/features/tasks";
import { getErrorMessage } from "@/shared/lib/errors";
import type { Task } from "@/features/tasks";
import type { TaskStatus } from "../types";

const TASK_STATUS_VALUES: readonly TaskStatus[] = [
    "BACKLOG",
    "TODO",
    "IN_PROGRESS",
    "IN_REVIEW",
    "DONE",
];

function isTaskStatus(value: string): value is TaskStatus {
    return TASK_STATUS_VALUES.includes(value as TaskStatus);
}

function buildOptimisticTaskList(
    allTasks: Task[],
    status: TaskStatus,
    reorderedStatusTasks: Task[],
): Task[] {
    const queue = [...reorderedStatusTasks];

    return allTasks.map((task) => {
        if (task.is_summary || task.status !== status) return task;
        const next = queue.shift();
        return next ?? task;
    });
}

interface KanbanDragParams {
    projectId: string | undefined;
    allTasks: Task[];
    allLeafTasksByStatus: Record<TaskStatus, Task[]>;
}

export function useKanbanDrag({ projectId, allTasks, allLeafTasksByStatus }: KanbanDragParams) {
    const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
    const { mutate } = useUpdateTask(projectId);
    const reorderTask = useReorderTask(projectId);

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    );

    const handleDragStart = useCallback((event: DragStartEvent) => {
        setActiveTaskId(event.active.id as string);
    }, []);

    const handleDragCancel = useCallback(() => {
        setActiveTaskId(null);
    }, []);

    const handleDragEnd = useCallback(
        (event: DragEndEvent) => {
            const { active, over } = event;
            setActiveTaskId(null);

            if (!over) return;

            const activeId = active.id as string;
            const currentStatus = active.data.current?.status as TaskStatus;
            const overId = over.id as string;
            const newStatus = isTaskStatus(overId)
                ? overId
                : (over.data.current?.status as TaskStatus | undefined);

            if (!newStatus) return;

            if (newStatus !== currentStatus) {
                mutate(
                    { taskId: activeId, data: { status: newStatus } },
                    { onError: (error) => toast.error(getErrorMessage(error)) },
                );
                return;
            }

            // Same-column drop on column container (not on another card): no-op.
            if (isTaskStatus(overId)) return;

            const statusTasks = allLeafTasksByStatus[currentStatus] ?? [];
            const oldIndex = statusTasks.findIndex((task) => task.id === activeId);
            const newIndex = statusTasks.findIndex((task) => task.id === overId);
            if (oldIndex < 0 || newIndex < 0 || oldIndex === newIndex) return;

            const activeTask = statusTasks[oldIndex];
            const overTask = statusTasks[newIndex];
            const activeParent = activeTask.parent_task_id ?? null;
            const overParent = overTask.parent_task_id ?? null;
            if (activeParent !== overParent) {
                toast.error("Can only reorder cards within the same task group");
                return;
            }

            const reorderedStatusTasks = arrayMove(statusTasks, oldIndex, newIndex);
            const optimisticData = buildOptimisticTaskList(
                allTasks,
                currentStatus,
                reorderedStatusTasks,
            );

            const afterTaskId = newIndex > 0 ? reorderedStatusTasks[newIndex - 1]?.id ?? null : null;
            const beforeTaskId = newIndex === 0 ? reorderedStatusTasks[1]?.id ?? null : null;

            reorderTask.mutate(
                {
                    taskId: activeId,
                    data: { after_task_id: afterTaskId, before_task_id: beforeTaskId },
                    optimisticData,
                },
                { onError: (error) => toast.error(getErrorMessage(error)) },
            );
        },
        [allLeafTasksByStatus, allTasks, mutate, reorderTask],
    );

    return { sensors, activeTaskId, handleDragStart, handleDragCancel, handleDragEnd };
}
