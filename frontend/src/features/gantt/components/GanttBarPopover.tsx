import { Popover, PopoverAnchor, PopoverContent } from "@/shared/ui/popover";
import type { Task } from "@/features/tasks";
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
  onClose,
}: GanttBarPopoverProps) {
  return (
    <Popover open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <PopoverAnchor asChild>
        {/* Invisible anchor exactly at the bar's x/y coordinate */}
        <div className="absolute pointer-events-none" style={{ left: x, top: y, width: 0, height: 0 }} />
      </PopoverAnchor>
      <PopoverContent
        data-slot="gantt-popover"
        side="bottom"
        align="start"
        sideOffset={8}
        className="w-auto p-3 text-xs space-y-1.5"
        style={{ border: "1px solid color-mix(in oklch, var(--border) 20%, transparent)" }}
        onInteractOutside={onClose}
        onEscapeKeyDown={onClose}
      >
        <div className="font-medium text-sm leading-tight">{task.name}</div>
        <div className="text-muted-foreground">WBS {task.wbs_code}</div>
        <div className="flex justify-between text-muted-foreground gap-4">
          <span>
            {format(new Date(task.start_date), "MM/dd/yyyy")} –{" "}
            {format(new Date(task.finish_date), "MM/dd/yyyy")}
          </span>
        </div>
        <div className="flex justify-between text-muted-foreground gap-4">
          <span>Duration: {task.duration}m</span>
          <span>Progress: {task.percent_complete}%</span>
        </div>
      </PopoverContent>
    </Popover>
  );
}
