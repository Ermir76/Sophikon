import { ChevronDown, ChevronRight, Diamond } from "lucide-react";

import type { Task } from "@/features/tasks";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/shared/ui/tooltip";
import type { GanttConfig } from "../types";
import { format } from "../utils/dateUtils";

interface GanttTableProps {
  tasks: Task[];
  config: GanttConfig;
  selectedTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  collapsedIds: Set<string>;
  onToggleCollapse: (taskId: string) => void;
}

export function GanttTableHeader() {
  return (
    <div className="flex h-full bg-muted/50 text-xs font-medium text-muted-foreground">
      <div className="flex w-14 shrink-0 items-center justify-center border-r">WBS</div>
      <div className="flex min-w-0 flex-1 items-center border-r px-2">Task Name</div>
      <div className="flex w-20 shrink-0 items-center justify-center border-r">Start</div>
      <div className="flex w-20 shrink-0 items-center justify-center border-r">Finish</div>
      <div className="flex w-12 shrink-0 items-center justify-center border-r">Dur.</div>
      <div className="flex w-12 shrink-0 items-center justify-center">Slack</div>
    </div>
  );
}

export function GanttTable({
  tasks,
  config,
  selectedTaskId,
  onTaskClick,
  collapsedIds,
  onToggleCollapse,
}: GanttTableProps) {
  return (
    <div>
      {tasks.map((task, i) => {
        const isSelected = task.id === selectedTaskId;

        return (
          <div
            key={task.id}
            className={`flex cursor-pointer border-b text-xs transition-colors hover:bg-muted/40 ${
              isSelected ? "bg-accent/50" : i % 2 !== 0 ? "bg-muted/15" : ""
            }`}
            style={{ height: config.rowHeight }}
            onClick={() => onTaskClick(task.id)}
          >
            <div className="flex w-14 shrink-0 items-center justify-center border-r text-muted-foreground">
              {task.wbs_code}
            </div>

            <div
              className="flex min-w-0 flex-1 items-center gap-1 overflow-hidden border-r px-2"
              style={{ paddingLeft: `${8 + task.outline_level * 16}px` }}
            >
              {task.is_summary ? (
                <button
                  className="flex size-4 shrink-0 items-center justify-center rounded bg-transparent outline-none hover:bg-muted/50"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleCollapse(task.id);
                  }}
                >
                  {collapsedIds.has(task.id) ? (
                    <ChevronRight className="size-3.5 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="size-3.5 text-muted-foreground" />
                  )}
                </button>
              ) : null}

              {task.is_milestone && <Diamond className="size-3 shrink-0 text-primary" />}

              <Tooltip>
                <TooltipTrigger asChild>
                  <span className={`truncate ${task.is_summary ? "font-semibold" : ""}`}>
                    {task.name}
                  </span>
                </TooltipTrigger>
                <TooltipContent side="bottom" sideOffset={4} className="max-w-xs">
                  <div className="space-y-0.5">
                    <div className="font-medium">{task.name}</div>
                    <div className="text-[10px] text-muted-foreground">
                      {task.wbs_code} · {format(new Date(task.start_date), "MM/dd/yyyy")} -{" "}
                      {format(new Date(task.finish_date), "MM/dd/yyyy")} · {task.duration}m
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            </div>

            <div className="flex w-20 shrink-0 items-center justify-center border-r text-muted-foreground">
              {format(new Date(task.start_date), "MM/dd")}
            </div>
            <div className="flex w-20 shrink-0 items-center justify-center border-r text-muted-foreground">
              {format(new Date(task.finish_date), "MM/dd")}
            </div>
            <div className="flex w-12 shrink-0 items-center justify-center border-r text-muted-foreground">
              {task.duration}m
            </div>
            <div className="flex w-12 shrink-0 items-center justify-center text-muted-foreground">
              {task.is_summary || task.is_milestone
                ? "-"
                : `${Math.round(task.total_slack / 480)}d`}
            </div>
          </div>
        );
      })}
    </div>
  );
}
