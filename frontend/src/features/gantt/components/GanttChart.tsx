import { useMemo } from "react";
import type { Task, Dependency } from "@/features/tasks/types";
import type { GanttConfig } from "../types";
import {
  dateToX,
  isWeekend,
  differenceInCalendarDays,
} from "../utils/dateUtils";
import { buildArrowPath } from "../utils/arrowPath";
import { eachDayOfInterval } from "date-fns";

interface GanttChartProps {
  tasks: Task[];
  dependencies: Dependency[];
  config: GanttConfig;
  pxPerDay: number;
  showCriticalPath: boolean;
  selectedTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  chartStartDate: Date;
  chartEndDate: Date;
  totalWidth: number;
}

export function GanttChart({
  tasks,
  dependencies,
  config,
  pxPerDay,
  showCriticalPath,
  selectedTaskId,
  onTaskClick,
  chartStartDate,
  chartEndDate,
  totalWidth,
}: GanttChartProps) {
  const todayX = useMemo(
    () => dateToX(new Date(), chartStartDate, pxPerDay),
    [chartStartDate, pxPerDay],
  );

  const weekendDays = useMemo(() => {
    if (pxPerDay < 8) return []; // skip at month zoom
    return eachDayOfInterval({ start: chartStartDate, end: chartEndDate }).filter(
      (d) => isWeekend(d),
    );
  }, [chartStartDate, chartEndDate, pxPerDay]);

  const taskMap = useMemo(() => {
    const map = new Map<string, { task: Task; index: number }>();
    tasks.forEach((t, i) => map.set(t.id, { task: t, index: i }));
    return map;
  }, [tasks]);

  const bodyHeight = tasks.length * config.rowHeight;
  const totalHeight = bodyHeight;

  return (
    <svg
      width={totalWidth}
      height={totalHeight}
      className="block select-none"
      style={{ pointerEvents: "none" }}
    >
      {/* Arrow markers */}
      <defs>
        <marker
          id="arrowhead"
          markerWidth="8"
          markerHeight="6"
          refX="8"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0, 8 3, 0 6" className="fill-muted-foreground" />
        </marker>
        <marker
          id="arrowhead-critical"
          markerWidth="8"
          markerHeight="6"
          refX="8"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0, 8 3, 0 6" className="fill-destructive" />
        </marker>
      </defs>

      {/* Row backgrounds */}
      {tasks.map((_, i) => (
        <rect
          key={`row-${i}`}
          x={0}
          y={i * config.rowHeight}
          width={totalWidth}
          height={config.rowHeight}
          className={i % 2 === 0 ? "fill-transparent" : "fill-muted/30"}
        />
      ))}

      {/* Row grid lines */}
      {tasks.map((_, i) => (
        <line
          key={`rowline-${i}`}
          x1={0}
          y1={(i + 1) * config.rowHeight}
          x2={totalWidth}
          y2={(i + 1) * config.rowHeight}
          className="stroke-border"
          strokeWidth={0.5}
        />
      ))}

      {/* Weekend shading */}
      {weekendDays.map((d, i) => {
        const x = dateToX(d, chartStartDate, pxPerDay);
        return (
          <rect
            key={`weekend-${i}`}
            x={x}
            y={0}
            width={pxPerDay}
            height={bodyHeight}
            className="fill-muted/20"
          />
        );
      })}

      {/* Today line */}
      {todayX >= 0 && todayX <= totalWidth && (
        <line
          x1={todayX}
          y1={0}
          x2={todayX}
          y2={bodyHeight}
          className="stroke-destructive"
          strokeWidth={2}
          strokeDasharray="6 3"
        />
      )}

      {/* Task bars */}
      {tasks.map((task, index) => {
        const y = index * config.rowHeight;
        const barY = y + (config.rowHeight - config.barHeight) / 2;
        const isSelected = task.id === selectedTaskId;
        const isCritical = showCriticalPath && task.is_critical;

        if (task.is_milestone) {
          return (
            <MilestoneMarker
              key={task.id}
              task={task}
              y={y}
              config={config}
              chartStartDate={chartStartDate}
              pxPerDay={pxPerDay}
              isCritical={isCritical}
              isSelected={isSelected}
              onClick={() => onTaskClick(task.id)}
            />
          );
        }

        if (task.is_summary) {
          return (
            <SummaryBar
              key={task.id}
              task={task}
              y={y}
              config={config}
              chartStartDate={chartStartDate}
              pxPerDay={pxPerDay}
              isCritical={isCritical}
              isSelected={isSelected}
              onClick={() => onTaskClick(task.id)}
            />
          );
        }

        const x = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
        const barWidth = Math.max(
          differenceInCalendarDays(
            new Date(task.finish_date),
            new Date(task.start_date),
          ) * pxPerDay,
          4,
        );
        const progressWidth = barWidth * (task.percent_complete / 100);

        return (
          <g
            key={task.id}
            className="cursor-pointer"
            style={{ pointerEvents: "auto" }}
            onClick={() => onTaskClick(task.id)}
          >
            <rect
              x={x}
              y={barY}
              width={barWidth}
              height={config.barHeight}
              rx={config.barRadius}
              ry={config.barRadius}
              className={isCritical ? "fill-destructive/70" : "fill-primary/70"}
              stroke={isSelected ? "hsl(var(--ring))" : "none"}
              strokeWidth={isSelected ? 2 : 0}
            />
            {progressWidth > 0 && (
              <rect
                x={x}
                y={barY}
                width={progressWidth}
                height={config.barHeight}
                rx={config.barRadius}
                ry={config.barRadius}
                className={isCritical ? "fill-destructive" : "fill-primary"}
              />
            )}
            {barWidth > 60 && (
              <text
                x={x + 6}
                y={barY + config.barHeight / 2}
                dy="0.35em"
                className="fill-primary-foreground text-[11px]"
                style={{ pointerEvents: "none" }}
              >
                {task.name.length > barWidth / 7
                  ? task.name.slice(0, Math.floor(barWidth / 7) - 1) + "\u2026"
                  : task.name}
              </text>
            )}
          </g>
        );
      })}

      {/* Dependency arrows */}
      {dependencies
        .filter((d) => !d.is_disabled)
        .map((dep) => {
          const pred = taskMap.get(dep.predecessor_id);
          const succ = taskMap.get(dep.successor_id);
          if (!pred || !succ) return null;

          const path = buildArrowPath(
            pred.task,
            succ.task,
            pred.index,
            succ.index,
            dep.type,
            chartStartDate,
            pxPerDay,
            config,
          );

          const isCritical =
            showCriticalPath && pred.task.is_critical && succ.task.is_critical;

          return (
            <path
              key={dep.id}
              d={path}
              fill="none"
              className={
                isCritical ? "stroke-destructive" : "stroke-muted-foreground"
              }
              strokeWidth={1.5}
              markerEnd={
                isCritical ? "url(#arrowhead-critical)" : "url(#arrowhead)"
              }
            />
          );
        })}
    </svg>
  );
}

// ── Sub-components ──

function MilestoneMarker({
  task,
  y,
  config,
  chartStartDate,
  pxPerDay,
  isCritical,
  isSelected,
  onClick,
}: {
  task: Task;
  y: number;
  config: GanttConfig;
  chartStartDate: Date;
  pxPerDay: number;
  isCritical: boolean;
  isSelected: boolean;
  onClick: () => void;
}) {
  const cx = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
  const cy = y + config.rowHeight / 2;
  const size = config.milestoneSize / 2;

  return (
    <g className="cursor-pointer" style={{ pointerEvents: "auto" }} onClick={onClick}>
      <rect
        x={cx - size}
        y={cy - size}
        width={config.milestoneSize}
        height={config.milestoneSize}
        rx={2}
        ry={2}
        transform={`rotate(45 ${cx} ${cy})`}
        className={isCritical ? "fill-destructive" : "fill-primary"}
        stroke={isSelected ? "hsl(var(--ring))" : "none"}
        strokeWidth={isSelected ? 2 : 0}
      />
    </g>
  );
}

function SummaryBar({
  task,
  y,
  config,
  chartStartDate,
  pxPerDay,
  isCritical,
  isSelected,
  onClick,
}: {
  task: Task;
  y: number;
  config: GanttConfig;
  chartStartDate: Date;
  pxPerDay: number;
  isCritical: boolean;
  isSelected: boolean;
  onClick: () => void;
}) {
  const x = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
  const barWidth = Math.max(
    differenceInCalendarDays(
      new Date(task.finish_date),
      new Date(task.start_date),
    ) * pxPerDay,
    4,
  );
  const cy = y + config.rowHeight / 2;
  const summaryHeight = 8;
  const triSize = 5;
  const fillClass = isCritical ? "fill-destructive" : "fill-primary";

  return (
    <g className="cursor-pointer" style={{ pointerEvents: "auto" }} onClick={onClick}>
      <rect
        x={x}
        y={cy - summaryHeight / 2}
        width={barWidth}
        height={summaryHeight}
        className={fillClass}
        stroke={isSelected ? "hsl(var(--ring))" : "none"}
        strokeWidth={isSelected ? 2 : 0}
      />
      <polygon
        points={`${x},${cy + summaryHeight / 2} ${x + triSize},${cy + summaryHeight / 2} ${x},${cy + summaryHeight / 2 + triSize}`}
        className={fillClass}
      />
      <polygon
        points={`${x + barWidth},${cy + summaryHeight / 2} ${x + barWidth - triSize},${cy + summaryHeight / 2} ${x + barWidth},${cy + summaryHeight / 2 + triSize}`}
        className={fillClass}
      />
    </g>
  );
}
