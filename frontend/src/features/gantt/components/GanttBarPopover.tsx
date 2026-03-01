import { useEffect, useRef } from "react";
import type { Task } from "@/features/tasks/types";
import { format } from "../utils/dateUtils";

interface GanttBarPopoverProps {
  task: Task;
  x: number;
  y: number;
  containerWidth: number;
  containerHeight: number;
  onClose: () => void;
}

export function GanttBarPopover({
  task,
  x,
  y,
  containerWidth,
  containerHeight,
  onClose,
}: GanttBarPopoverProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    function handleEsc(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEsc);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEsc);
    };
  }, [onClose]);

  // Position: prefer below-right, flip if near edges
  const cardWidth = 220;
  const cardHeight = 100;
  let left = x + 8;
  let top = y + 8;

  if (left + cardWidth > containerWidth) {
    left = x - cardWidth - 8;
  }
  if (top + cardHeight > containerHeight) {
    top = y - cardHeight - 8;
  }
  if (left < 0) left = 4;
  if (top < 0) top = 4;

  return (
    <div
      ref={ref}
      className="absolute z-50 rounded-md border border-border bg-popover text-popover-foreground shadow-md p-3 text-xs space-y-1.5"
      style={{ left, top, width: cardWidth, pointerEvents: "auto" }}
    >
      <div className="font-medium text-sm leading-tight">{task.name}</div>
      <div className="text-muted-foreground">WBS {task.wbs_code}</div>
      <div className="flex justify-between text-muted-foreground">
        <span>
          {format(new Date(task.start_date), "MM/dd/yyyy")} –{" "}
          {format(new Date(task.finish_date), "MM/dd/yyyy")}
        </span>
      </div>
      <div className="flex justify-between text-muted-foreground">
        <span>Duration: {task.duration}m</span>
        <span>Progress: {task.percent_complete}%</span>
      </div>
    </div>
  );
}
