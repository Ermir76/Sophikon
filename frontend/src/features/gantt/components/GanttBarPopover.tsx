import { useState } from "react";
import { toast } from "sonner";
import { Popover, PopoverAnchor, PopoverContent } from "@/shared/ui/popover";
import { Button } from "@/shared/ui/button";
import type { Task } from "@/features/tasks";
import { useUpdateTask } from "@/features/tasks";

interface GanttBarPopoverProps {
  task: Task;
  x: number;
  y: number;
  onClose: () => void;
}

const fieldClass =
  "w-full rounded border border-border bg-background px-2 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed";

export function GanttBarPopover({ task, x, y, onClose }: GanttBarPopoverProps) {
  const [name, setName] = useState(task.name);
  const [startDate, setStartDate] = useState(task.start_date.substring(0, 10));
  const [finishDate, setFinishDate] = useState(task.finish_date.substring(0, 10));
  const [duration, setDuration] = useState(String(task.duration));
  const [percent, setPercent] = useState(String(task.percent_complete));

  const updateTask = useUpdateTask(task.project_id);

  const isDirty =
    name !== task.name ||
    startDate !== task.start_date.substring(0, 10) ||
    finishDate !== task.finish_date.substring(0, 10) ||
    duration !== String(task.duration) ||
    percent !== String(task.percent_complete);

  const handleSave = async () => {
    try {
      await updateTask.mutateAsync({
        taskId: task.id,
        data: {
          name,
          start_date: startDate,
          finish_date: finishDate,
          duration: Math.max(0, Number(duration)),
          percent_complete: Math.min(100, Math.max(0, Number(percent))),
        },
      });
      onClose();
    } catch {
      toast.error("Failed to update task");
    }
  };

  return (
    <Popover open={true} onOpenChange={(open) => { if (!open) onClose(); }}>
      <PopoverAnchor asChild>
        <div className="absolute pointer-events-none" style={{ left: x, top: y, width: 0, height: 0 }} />
      </PopoverAnchor>
      <PopoverContent
        side="bottom"
        align="start"
        sideOffset={8}
        className="w-72 space-y-2.5 p-3 text-xs"
        style={{ border: "1px solid color-mix(in oklch, var(--border) 20%, transparent)" }}
        onInteractOutside={onClose}
        onEscapeKeyDown={onClose}
      >
        <div className="space-y-1">
          <div className="text-muted-foreground">Name</div>
          <input className={fieldClass} value={name} onChange={(e) => setName(e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <div className="text-muted-foreground">Start</div>
            <input
              type="date"
              className={fieldClass}
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              disabled={task.is_summary}
            />
          </div>
          <div className="space-y-1">
            <div className="text-muted-foreground">Finish</div>
            <input
              type="date"
              className={fieldClass}
              value={finishDate}
              onChange={(e) => setFinishDate(e.target.value)}
              disabled={task.is_summary}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <div className="text-muted-foreground">Duration (min)</div>
            <input
              type="number"
              min="0"
              className={fieldClass}
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              disabled={task.is_summary}
            />
          </div>
          <div className="space-y-1">
            <div className="text-muted-foreground">% Complete</div>
            <input
              type="number"
              min="0"
              max="100"
              className={fieldClass}
              value={percent}
              onChange={(e) => setPercent(e.target.value)}
            />
          </div>
        </div>

        <div className="text-muted-foreground">WBS {task.wbs_code}</div>

        {isDirty && (
          <div className="flex gap-2 pt-1">
            <Button
              size="sm"
              className="h-6 flex-1 text-xs"
              onClick={handleSave}
              disabled={updateTask.isPending}
            >
              {updateTask.isPending ? "Saving…" : "Save"}
            </Button>
            <Button size="sm" variant="outline" className="h-6 text-xs" onClick={onClose}>
              Cancel
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
