import { useLayoutEffect, useRef, useState } from "react";

import type { Task } from "@/features/tasks";
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

  useLayoutEffect(() => {
    if (!hoveredTaskId || !tooltipRef.current) return;

    const container = tooltipRef.current.parentElement;
    if (!container) return;

    const entry = taskMap.get(hoveredTaskId);
    if (!entry) return;

    const barX = dateToX(new Date(entry.task.start_date), chartStartDate, pxPerDay);
    const rightEdge = container.scrollLeft + container.clientWidth;
    setIsFlipped(rightEdge - barX < 360);
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
      className="pointer-events-none absolute z-40 rounded-md border bg-popover px-2.5 py-1.5 text-xs text-popover-foreground shadow-sm"
      style={{
        left: isFlipped ? barX - 12 : barX + 12,
        top: barY + 12,
        transform: isFlipped ? "translateX(-100%)" : "none",
        minWidth: 180,
        maxWidth: 240,
      }}
    >
      <div className="font-medium">{task.name}</div>
      <div className="text-[10px] text-muted-foreground">
        {format(new Date(task.start_date), "MM/dd")} -{" "}
        {format(new Date(task.finish_date), "MM/dd")} · {task.duration}m ·{" "}
        {task.percent_complete}%
      </div>
      {!task.is_summary &&
        !task.is_milestone &&
        (task.total_slack > 0 || task.free_slack > 0) && (
          <div className="text-[10px] text-muted-foreground">
            Slack: {Math.round(task.total_slack / 480)}d total ·{" "}
            {Math.round(task.free_slack / 480)}d free
          </div>
        )}
    </div>
  );
}
