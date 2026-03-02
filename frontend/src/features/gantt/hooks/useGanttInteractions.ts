import { useState, useCallback } from "react";

interface UseGanttInteractionsProps {
    onTaskClick: (taskId: string) => void;
    onZoomAtPoint: (deltaY: number, cursorX: number) => void;
    chartBodyRef: React.RefObject<HTMLDivElement | null>;
}

export function useGanttInteractions({
    onTaskClick,
    onZoomAtPoint,
    chartBodyRef,
}: UseGanttInteractionsProps) {
    const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);
    const [clickedTaskId, setClickedTaskId] = useState<string | null>(null);

    const handleTaskHover = useCallback((taskId: string | null) => {
        setHoveredTaskId(taskId);
    }, []);

    const handleChartTaskClick = useCallback(
        (taskId: string) => {
            setClickedTaskId((prev) => (prev === taskId ? null : taskId));
            onTaskClick(taskId);
        },
        [onTaskClick]
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
        clickedTaskId,
        setClickedTaskId,
        handleTaskHover,
        handleChartTaskClick,
        handleChartWheel,
    };
}
