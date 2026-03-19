import { useState, useCallback } from "react";
import { useSensors, useSensor, PointerSensor } from "@dnd-kit/core";
import type { DragStartEvent, DragEndEvent } from "@dnd-kit/core";
import { useUpdateTask } from "@/features/tasks";
import type { TaskStatus } from "../types";

export function useKanbanDrag(projectId: string | undefined) {
    const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
    const { mutate } = useUpdateTask(projectId);

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

            const newStatus = over.id as TaskStatus;
            const currentStatus = active.data.current?.status as TaskStatus;

            if (newStatus === currentStatus) return;

            mutate({
                taskId: active.id as string,
                data: { status: newStatus },
            });
        },
        [mutate],
    );

    return { sensors, activeTaskId, handleDragStart, handleDragCancel, handleDragEnd };
}
