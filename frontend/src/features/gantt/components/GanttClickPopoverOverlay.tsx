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
    chartBodyRef: React.RefObject<HTMLDivElement | null>;
    onClose: () => void;
}

export function GanttClickPopoverOverlay({
    clickedTaskId,
    taskMap,
    chartStartDate,
    pxPerDay,
    config,
    chartBodyRef,
    onClose,
}: GanttClickPopoverOverlayProps) {
    if (!clickedTaskId) return null;
    const entry = taskMap.get(clickedTaskId);
    if (!entry) return null;

    const { task, index } = entry;
    const barX = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
    const barY = index * config.rowHeight + config.rowHeight;
    const containerEl = chartBodyRef.current;
    const popoverContainerWidth = containerEl?.scrollWidth ?? 800;
    const popoverContainerHeight = containerEl?.scrollHeight ?? 600;

    return (
        <GanttBarPopover
            task={task}
            x={barX}
            y={barY}
            containerWidth={popoverContainerWidth}
            containerHeight={popoverContainerHeight}
            onClose={onClose}
        />
    );
}
