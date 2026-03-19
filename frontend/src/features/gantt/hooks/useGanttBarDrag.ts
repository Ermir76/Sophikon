import { useState, useEffect, useCallback, useRef } from "react";
import { addDays, differenceInCalendarDays, format } from "date-fns";
import type { Task } from "@/features/tasks";
import { useUpdateTask } from "@/features/tasks";

export interface DragState {
    taskId: string;
    dragMode: "move" | "resize-left" | "resize-right";
    originalStartDate: string;
    originalFinishDate: string;
    originalDuration: number;
    startClientX: number;
    deltaDays: number;
}

interface UseGanttBarDragProps {
    pxPerDay: number;
    projectId: string;
    onTaskClick: (taskId: string) => void;
}

export function useGanttBarDrag({ pxPerDay, projectId, onTaskClick }: UseGanttBarDragProps) {
    const [dragState, setDragState] = useState<DragState | null>(null);
    const dragStateRef = useRef<DragState | null>(null);
    const pxPerDayRef = useRef(pxPerDay);
    pxPerDayRef.current = pxPerDay;

    const updateTask = useUpdateTask(projectId);
    const mutateRef = useRef(updateTask.mutate);
    mutateRef.current = updateTask.mutate;
    const onTaskClickRef = useRef(onTaskClick);
    onTaskClickRef.current = onTaskClick;

    const startDrag = useCallback(
        (e: React.PointerEvent, task: Task, mode: DragState["dragMode"]) => {
            e.stopPropagation();
            (e.currentTarget as Element).setPointerCapture(e.pointerId);
            const state: DragState = {
                taskId: task.id,
                dragMode: mode,
                originalStartDate: task.start_date,
                originalFinishDate: task.finish_date,
                originalDuration: task.duration,
                startClientX: e.clientX,
                deltaDays: 0,
            };
            dragStateRef.current = state;
            setDragState(state);
        },
        [],
    );

    const isActive = dragState !== null;

    useEffect(() => {
        if (!isActive) return;

        const onMove = (e: PointerEvent) => {
            const ds = dragStateRef.current;
            if (!ds) return;
            const rawDelta = e.clientX - ds.startClientX;
            const newDeltaDays =
                Math.abs(rawDelta) < 4 ? 0 : Math.round(rawDelta / pxPerDayRef.current);
            if (newDeltaDays === ds.deltaDays) return;
            const updated = { ...ds, deltaDays: newDeltaDays };
            dragStateRef.current = updated;
            setDragState(updated);
        };

        const onUp = () => {
            const ds = dragStateRef.current;
            dragStateRef.current = null;
            setDragState(null);
            if (!ds) return;
            if (ds.deltaDays === 0) {
                // No movement — treat as a click, but only for the bar body (not resize handles)
                if (ds.dragMode === "move") onTaskClickRef.current(ds.taskId);
                return;
            }

            const origStart = new Date(ds.originalStartDate);
            const origFinish = new Date(ds.originalFinishDate);
            const origSpan = differenceInCalendarDays(origFinish, origStart) + 1;

            let data: { start_date?: string; finish_date?: string; duration?: number } = {};

            if (ds.dragMode === "move") {
                data = {
                    start_date: format(addDays(origStart, ds.deltaDays), "yyyy-MM-dd"),
                    finish_date: format(addDays(origFinish, ds.deltaDays), "yyyy-MM-dd"),
                };
            } else if (ds.dragMode === "resize-right") {
                const newDuration = Math.max(1, origSpan + ds.deltaDays);
                data = {
                    finish_date: format(addDays(origStart, newDuration - 1), "yyyy-MM-dd"),
                    duration: newDuration * 480, // backend stores duration in minutes (8h/day default)
                };
            } else {
                // resize-left: dragging left (negative deltaDays) extends the bar leftward
                const newDuration = Math.max(1, origSpan - ds.deltaDays);
                data = {
                    start_date: format(addDays(origFinish, -(newDuration - 1)), "yyyy-MM-dd"),
                    duration: newDuration * 480, // backend stores duration in minutes (8h/day default)
                };
            }

            mutateRef.current({ taskId: ds.taskId, data });
        };

        document.addEventListener("pointermove", onMove);
        document.addEventListener("pointerup", onUp);
        return () => {
            document.removeEventListener("pointermove", onMove);
            document.removeEventListener("pointerup", onUp);
        };
    }, [isActive]); // eslint-disable-line react-hooks/exhaustive-deps

    return { dragState, startDrag };
}
