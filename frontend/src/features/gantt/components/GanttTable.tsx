import { ChevronDown, ChevronRight, Diamond } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/ui/tooltip";
import type { Task } from "@/features/tasks";
import type { GanttConfig } from "../types";
import { format } from "../utils/dateUtils";
import { useGanttColumns } from "../hooks/useGanttColumns";
import { ColumnResizeHandle } from "./ColumnResizeHandle";

const INDENT_PX = 16;

// For each task at index i, determine which ancestor levels have more siblings after it.
// flags[k] = true means level k+1 (1-indexed) has a continuing sibling → render full |
// flags[k] = false means it's the last at that level → render └
function buildGuideFlags(tasks: Task[], taskIndex: number): boolean[] {
  const task = tasks[taskIndex];
  const depth = task.outline_level - 1; // number of guide lines needed
  if (depth <= 0) return [];

  const flags: boolean[] = [];
  for (let k = 1; k <= depth; k++) {
    let hasSibling = false;
    for (let j = taskIndex + 1; j < tasks.length; j++) {
      const lvl = tasks[j].outline_level;
      if (lvl < k) break;
      if (lvl === k) { hasSibling = true; break; }
    }
    flags.push(hasSibling);
  }
  return flags;
}

interface GanttTableProps {
  tasks: Task[];
  config: GanttConfig;
  selectedTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  collapsedIds: Set<string>;
  onToggleCollapse: (taskId: string) => void;
}

export function GanttTableHeader() {
  const { visibleColumns, setColumnWidth } = useGanttColumns();

  return (
    <div className="flex h-full min-w-max bg-muted/50 text-xs font-medium text-muted-foreground">
      {visibleColumns.map((col, i) => (
        <div
          key={col.id}
          className="relative flex shrink-0 items-center justify-center border-r px-2 last:border-r-0"
          style={{ width: col.width }}
        >
          <span className="truncate">{col.label}</span>
          {i < visibleColumns.length - 1 && (
            <ColumnResizeHandle
              columnId={col.id}
              currentWidth={col.width}
              minWidth={col.minWidth}
              onResize={setColumnWidth}
            />
          )}
        </div>
      ))}
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
  const { visibleColumns, setColumnWidth } = useGanttColumns();
  const nameCol = visibleColumns.find((c) => c.id === "name");

  return (
    <div>
      {tasks.map((task, i) => {
        const isSelected = task.id === selectedTaskId;
        const guideFlags = buildGuideFlags(tasks, i);
        const paddingLeft = 8 + (task.outline_level - 1) * INDENT_PX;

        return (
          <div
            key={task.id}
            className={`flex min-w-max cursor-pointer border-b text-xs transition-colors hover:bg-muted/40 ${
              isSelected ? "bg-accent/50" : i % 2 !== 0 ? "bg-muted/15" : ""
            }`}
            style={{ height: config.rowHeight }}
            onClick={() => onTaskClick(task.id)}
          >
            {visibleColumns.map((col, colIdx) => {
              if (col.id === "name") {
                return (
                  <div
                    key={col.id}
                    className="relative flex shrink-0 items-center overflow-hidden border-r"
                    style={{ width: nameCol?.width ?? col.width }}
                  >
                    {/* Tree guide lines */}
                    {guideFlags.map((hasSibling, k) => {
                      const x = 8 + k * INDENT_PX;
                      const isImmediate = k === guideFlags.length - 1;
                      return (
                        <div key={k}>
                          <div
                            className="absolute w-px bg-border/50"
                            style={{
                              left: x,
                              top: 0,
                              height: isImmediate && !hasSibling ? "50%" : "100%",
                            }}
                          />
                          {isImmediate && (
                            <div
                              className="absolute h-px bg-border/50"
                              style={{ left: x, top: "50%", width: INDENT_PX }}
                            />
                          )}
                        </div>
                      );
                    })}

                    {/* Content */}
                    <div
                      className="flex min-w-0 items-center gap-1"
                      style={{ paddingLeft }}
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
                              {task.wbs_code} · {format(new Date(task.start_date), "MM/dd/yyyy")} –{" "}
                              {format(new Date(task.finish_date), "MM/dd/yyyy")} · {task.duration}m
                            </div>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </div>

                    <ColumnResizeHandle
                      columnId={col.id}
                      currentWidth={col.width}
                      minWidth={col.minWidth}
                      onResize={setColumnWidth}
                    />
                  </div>
                );
              }

              const isLast = colIdx === visibleColumns.length - 1;
              let content: React.ReactNode = null;
              if (col.id === "wbs") content = <span className="text-muted-foreground truncate">{task.wbs_code}</span>;
              else if (col.id === "start") content = <span className="text-muted-foreground">{format(new Date(task.start_date), "MM/dd")}</span>;
              else if (col.id === "finish") content = <span className="text-muted-foreground">{format(new Date(task.finish_date), "MM/dd")}</span>;
              else if (col.id === "dur") content = <span className="text-muted-foreground">{task.duration}m</span>;
              else if (col.id === "slack") content = <span className="text-muted-foreground">{task.is_summary || task.is_milestone ? "-" : `${Math.round(task.total_slack / 480)}d`}</span>;

              return (
                <div
                  key={col.id}
                  className={`relative flex shrink-0 items-center justify-center overflow-hidden px-1 ${isLast ? "" : "border-r"}`}
                  style={{ width: col.width }}
                >
                  {content}
                  {!isLast && (
                    <ColumnResizeHandle
                      columnId={col.id}
                      currentWidth={col.width}
                      minWidth={col.minWidth}
                      onResize={setColumnWidth}
                    />
                  )}
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
