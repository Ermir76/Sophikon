import { useState, useCallback, useRef } from "react";

interface UseGanttInteractionsProps {
    onTaskClick: (taskId: string) => void;
    onTaskDoubleClick: (taskId: string) => void;
    onZoomAtPoint: (deltaY: number, cursorX: number) => void;
    chartBodyRef: React.RefObject<HTMLDivElement | null>;
}

export function useGanttInteractions({
    onTaskClick,
    onTaskDoubleClick,
    onZoomAtPoint,
    chartBodyRef,
}: UseGanttInteractionsProps) {
    const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);
    const clickTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const handleTaskHover = useCallback((taskId: string | null) => {
        setHoveredTaskId(taskId);
    }, []);

    const handleChartTaskClick = useCallback(
        (taskId: string) => {
            if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
            clickTimerRef.current = setTimeout(() => {
                clickTimerRef.current = null;
                onTaskClick(taskId);
            }, 200);
        },
        [onTaskClick]
    );

    const handleChartTaskDoubleClick = useCallback(
        (taskId: string) => {
            if (clickTimerRef.current) {
                clearTimeout(clickTimerRef.current);
                clickTimerRef.current = null;
            }
            onTaskDoubleClick(taskId);
        },
        [onTaskDoubleClick]
    );

    const handleChartWheel = useCallback(
        (e: React.WheelEvent<HTMLDivElement>) => {
            e.preventDefault();

            if (e.ctrlKey || e.metaKey) {
                // Zoom at cursor
                const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
                const cursorX = e.clientX - rect.left + (chartBodyRef.current?.scrollLeft ?? 0);
                onZoomAtPoint(e.deltaY, cursorX);
                return;
            }

            const cb = chartBodyRef.current;
            if (!cb) return;

            if (e.shiftKey) {
                cb.scrollLeft += e.deltaY;
            } else {
                cb.scrollTop += e.deltaY;
                cb.scrollLeft += e.deltaX;
            }
        },
        [onZoomAtPoint, chartBodyRef]
    );

    return {
        hoveredTaskId,
        setHoveredTaskId,
        handleTaskHover,
        handleChartTaskClick,
        handleChartTaskDoubleClick,
        handleChartWheel,
    };
}
