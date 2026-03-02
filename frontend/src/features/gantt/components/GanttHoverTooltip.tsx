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
    if (!hoveredTaskId) return null;
    const entry = taskMap.get(hoveredTaskId);
    if (!entry) return null;

    const { task, index } = entry;
    const barX = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
    const barY = index * config.rowHeight + config.rowHeight / 2;

    return (
        <div
            className="absolute z-40 rounded-md bg-foreground text-background px-2.5 py-1.5 text-xs pointer-events-none shadow-md"
            style={{
                left: barX + 12,
                top: barY + 12,
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
