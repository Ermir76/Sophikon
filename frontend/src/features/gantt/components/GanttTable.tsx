import React from "react";
import { Diamond, ChevronDown, ChevronRight } from "lucide-react";
import type { Task } from "@/features/tasks/types";
import type { GanttConfig } from "../types";
import { format } from "../utils/dateUtils";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/shared/ui/tooltip";

interface GanttTableProps {
  tasks: Task[];
  config: GanttConfig;
  selectedTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  collapsedIds: Set<string>;
  onToggleCollapse: (taskId: string) => void;
  scrollRef: React.RefObject<HTMLDivElement | null>;
  onScroll: (e: React.UIEvent<HTMLDivElement>) => void;
}

export function GanttTableHeader() {
  return (
    <div
      className="flex h-full bg-muted/50 text-xs font-medium text-muted-foreground"
    >
      <div className="w-14 shrink-0 flex items-center justify-center border-r border-border">
        WBS
      </div>
      <div className="flex-1 min-w-0 flex items-center px-2 border-r border-border">
        Task Name
      </div>
      <div className="w-20 shrink-0 flex items-center justify-center border-r border-border">
        Start
      </div>
      <div className="w-20 shrink-0 flex items-center justify-center border-r border-border">
        Finish
      </div>
      <div className="w-12 shrink-0 flex items-center justify-center">
        Dur.
      </div>
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
  scrollRef,
  onScroll,
}: GanttTableProps) {
  return (
    <div
      ref={scrollRef}
      className="h-full overflow-y-auto overflow-x-hidden"
      onScroll={onScroll}
    >
      {tasks.map((task, i) => {
          const isSelected = task.id === selectedTaskId;
          return (
            <div
              key={task.id}
              className={`flex border-b border-border text-xs cursor-pointer hover:bg-muted/40 transition-colors ${
                isSelected ? "bg-accent/50" : i % 2 !== 0 ? "bg-muted/15" : ""
              }`}
              style={{ height: config.rowHeight }}
              onClick={() => onTaskClick(task.id)}
            >
              <div className="w-14 shrink-0 flex items-center justify-center border-r border-border text-muted-foreground">
                {task.wbs_code}
              </div>
              <div
                className="flex-1 min-w-0 flex items-center px-2 border-r border-border gap-1 overflow-hidden"
                style={{ paddingLeft: `${8 + task.outline_level * 16}px` }}
              >
                {task.is_summary ? (
                  <button
                    className="shrink-0 flex items-center justify-center size-4 hover:bg-muted/50 rounded border-none bg-transparent outline-none"
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
                {task.is_milestone && (
                  <Diamond className="size-3 shrink-0 text-primary" />
                )}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span
                      className={`truncate ${task.is_summary ? "font-semibold" : ""}`}
                    >
                      {task.name}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" sideOffset={4} className="max-w-xs">
                    <div className="space-y-0.5">
                      <div className="font-medium">{task.name}</div>
                      <div className="text-[10px] opacity-80">
                        {task.wbs_code} · {format(new Date(task.start_date), "MM/dd/yyyy")} – {format(new Date(task.finish_date), "MM/dd/yyyy")} · {task.duration}m
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </div>
              <div className="w-20 shrink-0 flex items-center justify-center border-r border-border text-muted-foreground">
                {format(new Date(task.start_date), "MM/dd")}
              </div>
              <div className="w-20 shrink-0 flex items-center justify-center border-r border-border text-muted-foreground">
                {format(new Date(task.finish_date), "MM/dd")}
              </div>
              <div className="w-12 shrink-0 flex items-center justify-center text-muted-foreground">
                {task.duration}m
              </div>
            </div>
          );
        })}
    </div>
  );
}
