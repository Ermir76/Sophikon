import { useLayoutEffect, useRef, useState } from "react";
import type { Task } from "@/features/tasks/types";
import type { GanttConfig } from "../types";
import { dateToX, format } from "../utils/dateUtils";

interface GanttHoverTooltipProps {
    hoveredTaskId: string | null;
    taskMap: Map<string, { task: Task; index: number }>;
    chartStartDate: Date;
    pxPerDay: number;
    config: GanttConfig;
}

export function GanttHoverTooltip({
    hoveredTaskId,
    taskMap,
    chartStartDate,
    pxPerDay,
    config,
}: GanttHoverTooltipProps) {
    const tooltipRef = useRef<HTMLDivElement>(null);
    const [isFlipped, setIsFlipped] = useState(false);

    // Evaluate flip requirement whenever the hovered task changes
    useLayoutEffect(() => {
        if (!hoveredTaskId || !tooltipRef.current) return;

        // The nearest parent is the scrolling timeline view in GanttContainer
        const container = tooltipRef.current.parentElement;
        if (!container) return;

        const entry = taskMap.get(hoveredTaskId);
        if (entry) {
            const barX = dateToX(new Date(entry.task.start_date), chartStartDate, pxPerDay);
            const rightEdge = container.scrollLeft + container.clientWidth;

            // If the start of the bar is within 360px of the visible right edge of the window
            if (rightEdge - barX < 360) {
                setIsFlipped(true);
            } else {
                setIsFlipped(false);
            }
        }
    }, [hoveredTaskId, taskMap, chartStartDate, pxPerDay]);

    if (!hoveredTaskId) return null;
    const entry = taskMap.get(hoveredTaskId);
    if (!entry) return null;

    const { task, index } = entry;
    const barX = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
    const barY = index * config.rowHeight + config.rowHeight / 2;

    return (
        <div
            ref={tooltipRef}
            className="absolute z-40 rounded-md bg-foreground text-background px-2.5 py-1.5 text-xs pointer-events-none shadow-md"
            style={{
                left: isFlipped ? barX - 12 : barX + 12,
                top: barY + 12,
                transform: isFlipped ? "translateX(-100%)" : "none",
                minWidth: 180,
                maxWidth: 240,
            }}
        >
            <div className="font-medium">{task.name}</div>
            <div className="opacity-80 text-[10px]">
                {format(new Date(task.start_date), "MM/dd")} – {format(new Date(task.finish_date), "MM/dd")} · {task.duration}m · {task.percent_complete}%
            </div>
        </div>
    );
}
