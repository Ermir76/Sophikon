import type { Task } from "@/features/tasks";
import type { GanttConfig } from "../types";
import { dateToX } from "../utils/dateUtils";
import { GanttBarPopover } from "./GanttBarPopover";

interface GanttClickPopoverOverlayProps {
    clickedTaskId: string | null;
    taskMap: Map<string, { task: Task; index: number }>;
    chartStartDate: Date;
    pxPerDay: number;
    config: GanttConfig;
    onClose: () => void;
}

export function GanttClickPopoverOverlay({
    clickedTaskId,
    taskMap,
    chartStartDate,
    pxPerDay,
    config,
    onClose,
}: GanttClickPopoverOverlayProps) {
    if (!clickedTaskId) return null;
    const entry = taskMap.get(clickedTaskId);
    if (!entry) return null;

    const { task, index } = entry;
    const barX = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
    const barY = index * config.rowHeight + config.rowHeight;

    return (
        <GanttBarPopover
            task={task}
            x={barX}
            y={barY}
            onClose={onClose}
        />
    );
}
