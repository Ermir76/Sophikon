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
    const hoverOffTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const handleTaskHover = useCallback((taskId: string | null) => {
        if (taskId !== null) {
            if (hoverOffTimerRef.current) {
                clearTimeout(hoverOffTimerRef.current);
                hoverOffTimerRef.current = null;
            }
            setHoveredTaskId(taskId);
        } else {
            hoverOffTimerRef.current = setTimeout(() => {
                hoverOffTimerRef.current = null;
                setHoveredTaskId(null);
            }, 400);
        }
    }, []);

    const handleChartTaskClick = useCallback(
        (taskId: string) => {
            onTaskClick(taskId);
        },
        [onTaskClick]
    );

    const handleChartTaskDoubleClick = useCallback(
        (taskId: string) => {
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
