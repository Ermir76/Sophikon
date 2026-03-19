import { useState, useEffect, useCallback, useRef } from "react";
import type { Task } from "@/features/tasks";
import { useCreateDependency } from "@/features/tasks";

export interface DepDragState {
    sourceTaskId: string;
    sourceEdge: "start" | "finish";
    fromX: number;
    fromY: number;
    currentX: number;
    currentY: number;
    targetTaskId: string | null;
}

interface UseGanttDependencyDragProps {
    projectId: string;
    tasks: Task[];
    rowHeight: number;
    headerHeight: number;
    getTimelineEl: () => HTMLDivElement | null;
}

export function useGanttDependencyDrag({
    projectId,
    tasks,
    rowHeight,
    headerHeight,
    getTimelineEl,
}: UseGanttDependencyDragProps) {
    const [depDragState, setDepDragState] = useState<DepDragState | null>(null);
    const depDragRef = useRef<DepDragState | null>(null);
    const tasksRef = useRef(tasks);
    tasksRef.current = tasks;

    const createDependency = useCreateDependency(projectId);
    const createMutateRef = useRef(createDependency.mutate);
    createMutateRef.current = createDependency.mutate;

    const startConnectorDrag = useCallback(
        (
            e: React.PointerEvent,
            sourceTaskId: string,
            sourceEdge: "start" | "finish",
            fromX: number,
            fromY: number,
        ) => {
            e.stopPropagation();
            (e.currentTarget as Element).setPointerCapture(e.pointerId);
            const state: DepDragState = {
                sourceTaskId,
                sourceEdge,
                fromX,
                fromY,
                currentX: fromX,
                currentY: fromY,
                targetTaskId: null,
            };
            depDragRef.current = state;
            setDepDragState(state);
        },
        [],
    );

    const isActive = depDragState !== null;

    useEffect(() => {
        if (!isActive) return;

        const toSvgCoords = (clientX: number, clientY: number) => {
            const el = getTimelineEl();
            if (!el) return { x: clientX, y: clientY };
            const rect = el.getBoundingClientRect();
            return {
                x: clientX - rect.left + el.scrollLeft,
                y: clientY - rect.top + el.scrollTop - headerHeight,
            };
        };

        const onMove = (e: PointerEvent) => {
            const ds = depDragRef.current;
            if (!ds) return;
            const { x: svgX, y: svgY } = toSvgCoords(e.clientX, e.clientY);
            const targetIndex = Math.floor(svgY / rowHeight);
            const targetTask = tasksRef.current[targetIndex];
            const targetTaskId =
                targetTask && targetTask.id !== ds.sourceTaskId ? targetTask.id : null;
            const updated: DepDragState = { ...ds, currentX: svgX, currentY: svgY, targetTaskId };
            depDragRef.current = updated;
            setDepDragState(updated);
        };

        const onUp = () => {
            const ds = depDragRef.current;
            depDragRef.current = null;
            setDepDragState(null);
            if (!ds || !ds.targetTaskId) return;
            createMutateRef.current({
                predecessor_id: ds.sourceTaskId,
                successor_id: ds.targetTaskId,
                type: ds.sourceEdge === "finish" ? "FS" : "SS",
            });
        };

        document.addEventListener("pointermove", onMove);
        document.addEventListener("pointerup", onUp);
        return () => {
            document.removeEventListener("pointermove", onMove);
            document.removeEventListener("pointerup", onUp);
        };
    }, [isActive]); // eslint-disable-line react-hooks/exhaustive-deps

    return { depDragState, startConnectorDrag };
}
