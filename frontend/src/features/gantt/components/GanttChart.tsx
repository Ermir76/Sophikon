import { useMemo, Fragment } from "react";
import type { Task, Dependency } from "@/features/tasks";
import type { GanttConfig } from "../types";
import {
  dateToX,
  isWeekend,
  taskSpanWidthPx,
  differenceInCalendarDays,
} from "../utils/dateUtils";
import { buildArrowPath } from "../utils/arrowPath";
import { eachDayOfInterval } from "date-fns";
import type { DragState } from "../hooks/useGanttBarDrag";
import type { DepDragState } from "../hooks/useGanttDependencyDrag";

interface GanttChartProps {
  tasks: Task[];
  dependencies: Dependency[];
  config: GanttConfig;
  pxPerDay: number;
  showCriticalPath: boolean;
  selectedTaskId: string | null;
  hoveredTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  onTaskDoubleClick: (taskId: string) => void;
  onTaskHover: (taskId: string | null) => void;
  chartStartDate: Date;
  chartEndDate: Date;
  totalWidth: number;
  colorMap?: Map<string, string | null>;
  dragState: DragState | null;
  onBarDragStart: (e: React.PointerEvent, task: Task, mode: DragState["dragMode"]) => void;
  onTaskContextMenu: (e: React.MouseEvent, taskId: string) => void;
  depDragState: DepDragState | null;
  onConnectorDragStart: (e: React.PointerEvent, sourceTaskId: string, sourceEdge: "start" | "finish", fromX: number, fromY: number) => void;
  onDependencyContextMenu: (e: React.MouseEvent, depId: string) => void;
}

export function GanttChart({
  tasks,
  dependencies,
  config,
  pxPerDay,
  showCriticalPath,
  selectedTaskId,
  hoveredTaskId,
  onTaskClick,
  onTaskDoubleClick,
  onTaskHover,
  chartStartDate,
  chartEndDate,
  totalWidth,
  colorMap,
  dragState,
  onBarDragStart,
  onTaskContextMenu,
  depDragState,
  onConnectorDragStart,
  onDependencyContextMenu,
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

  return (
    <svg
      width={totalWidth}
      height={bodyHeight}
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

      {/* Dependency arrows — rendered before bars so they appear behind */}
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
            <g key={dep.id}>
              {/* Visible arrow */}
              <path
                d={path}
                fill="none"
                className={isCritical ? "stroke-destructive" : "stroke-muted-foreground"}
                strokeWidth={1}
                strokeOpacity={0.6}
                markerEnd={isCritical ? "url(#arrowhead-critical)" : "url(#arrowhead)"}
                style={{ pointerEvents: "none" }}
              />
              {/* Invisible fat hit area for right-click */}
              <path
                d={path}
                fill="none"
                stroke="transparent"
                strokeWidth={12}
                style={{ pointerEvents: "auto", cursor: "context-menu" }}
                onContextMenu={(e) => { e.preventDefault(); onDependencyContextMenu(e, dep.id); }}
              />
            </g>
          );
        })}

      {/* Task bars */}
      {tasks.map((task, index) => {
        const y = index * config.rowHeight;
        const barY = y + (config.rowHeight - config.barHeight) / 2;
        const isSelected = task.id === selectedTaskId;
        const isCritical = showCriticalPath && task.is_critical;
        const taskColor = !isCritical ? (colorMap?.get(task.id) ?? null) : null;

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
              color={taskColor}
              isHovered={hoveredTaskId === task.id}
              depDragTargeted={depDragState?.targetTaskId === task.id}
              onClick={() => onTaskClick(task.id)}
              onDoubleClick={() => onTaskDoubleClick(task.id)}
              onMouseEnter={() => onTaskHover(task.id)}
              onMouseLeave={() => onTaskHover(null)}
              onContextMenu={(e) => { e.preventDefault(); onTaskContextMenu(e, task.id); }}
              onConnectorDragStart={onConnectorDragStart}
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
              color={taskColor}
              onClick={() => onTaskClick(task.id)}
              onDoubleClick={() => onTaskDoubleClick(task.id)}
              onMouseEnter={() => onTaskHover(task.id)}
              onMouseLeave={() => onTaskHover(null)}
              onContextMenu={(e) => { e.preventDefault(); onTaskContextMenu(e, task.id); }}
            />
          );
        }

        const x = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
        const barWidth = taskSpanWidthPx(
          new Date(task.start_date),
          new Date(task.finish_date),
          pxPerDay,
        );
        const progressWidth = barWidth * (task.percent_complete / 100);

        const isDragged = dragState?.taskId === task.id;
        let ghostX = x;
        let ghostBarWidth = barWidth;
        if (isDragged && dragState) {
          const origSpan =
            differenceInCalendarDays(
              new Date(dragState.originalFinishDate),
              new Date(dragState.originalStartDate),
            ) + 1;
          if (dragState.dragMode === "move") {
            ghostX = x + dragState.deltaDays * pxPerDay;
          } else if (dragState.dragMode === "resize-right") {
            ghostBarWidth = Math.max(1, origSpan + dragState.deltaDays) * pxPerDay;
          } else {
            const newSpan = Math.max(1, origSpan - dragState.deltaDays);
            ghostX = x + dragState.deltaDays * pxPerDay;
            ghostBarWidth = newSpan * pxPerDay;
          }
        }

        return (
          <Fragment key={task.id}>
            <g
              className="cursor-grab"
              style={{ pointerEvents: "auto", opacity: isDragged ? 0.4 : 1 }}
              onDoubleClick={() => onTaskDoubleClick(task.id)}
              onMouseEnter={() => onTaskHover(task.id)}
              onMouseLeave={() => onTaskHover(null)}
              onPointerDown={(e) => onBarDragStart(e, task, "move")}
              onContextMenu={(e) => { e.preventDefault(); onTaskContextMenu(e, task.id); }}
            >
              {/* Background bar */}
              <rect
                x={x}
                y={barY}
                width={barWidth}
                height={config.barHeight}
                rx={config.barRadius}
                ry={config.barRadius}
                className={isCritical ? "fill-destructive/70" : undefined}
                style={
                  isCritical
                    ? undefined
                    : taskColor
                      ? { fill: taskColor, fillOpacity: 0.45 }
                      : { fill: "transparent", stroke: "var(--border)", strokeWidth: 1.5 }
                }
                stroke={isSelected ? "hsl(var(--ring))" : undefined}
                strokeWidth={isSelected ? 2 : undefined}
              />
              {/* Progress bar */}
              {progressWidth > 0 && (
                <rect
                  x={x}
                  y={barY}
                  width={progressWidth}
                  height={config.barHeight}
                  rx={config.barRadius}
                  ry={config.barRadius}
                  className={isCritical ? "fill-destructive" : undefined}
                  style={
                    isCritical
                      ? undefined
                      : taskColor
                        ? { fill: taskColor, fillOpacity: 0.85 }
                        : { fill: "var(--foreground)", fillOpacity: 0.15 }
                  }
                />
              )}
              {/* Label */}
              {barWidth > 60 && (
                <text
                  x={x + 6}
                  y={barY + config.barHeight / 2}
                  dy="0.35em"
                  className={isCritical ? "fill-primary-foreground text-[11px]" : (taskColor ? "text-[11px]" : "fill-foreground text-[11px]")}
                  style={taskColor && !isCritical ? { fill: "#fff", pointerEvents: "none" } : { pointerEvents: "none" }}
                >
                  {task.name.length > barWidth / 7
                    ? task.name.slice(0, Math.floor(barWidth / 7) - 1) + "\u2026"
                    : task.name}
                </text>
              )}
              {/* Resize handles — rendered last to win hit-test over the bar body */}
              <rect
                x={x}
                y={barY}
                width={6}
                height={config.barHeight}
                style={{ fill: "transparent", cursor: "w-resize" }}
                onPointerDown={(e) => { e.stopPropagation(); onBarDragStart(e, task, "resize-left"); }}
              />
              <rect
                x={x + barWidth - 6}
                y={barY}
                width={6}
                height={config.barHeight}
                style={{ fill: "transparent", cursor: "e-resize" }}
                onPointerDown={(e) => { e.stopPropagation(); onBarDragStart(e, task, "resize-right"); }}
              />
            </g>
            {/* Connector dots — siblings of bar <g> so they have independent hover, no gap problem */}
            {hoveredTaskId === task.id && (
              <>
                <circle
                  cx={x - 8}
                  cy={barY + config.barHeight / 2}
                  r={6}
                  className="fill-primary stroke-background"
                  strokeWidth={1.5}
                  style={{ cursor: "crosshair", pointerEvents: "auto" }}
                  onMouseEnter={() => onTaskHover(task.id)}
                  onMouseLeave={() => onTaskHover(null)}
                  onPointerDown={(e) => onConnectorDragStart(e, task.id, "start", x - 8, barY + config.barHeight / 2)}
                />
                <circle
                  cx={x + barWidth + 8}
                  cy={barY + config.barHeight / 2}
                  r={6}
                  className="fill-primary stroke-background"
                  strokeWidth={1.5}
                  style={{ cursor: "crosshair", pointerEvents: "auto" }}
                  onMouseEnter={() => onTaskHover(task.id)}
                  onMouseLeave={() => onTaskHover(null)}
                  onPointerDown={(e) => onConnectorDragStart(e, task.id, "finish", x + barWidth + 8, barY + config.barHeight / 2)}
                />
              </>
            )}
            {/* Ghost bar — shows preview position during drag */}
            {isDragged && dragState && (
              <rect
                x={ghostX}
                y={barY}
                width={Math.max(ghostBarWidth, 4)}
                height={config.barHeight}
                rx={config.barRadius}
                ry={config.barRadius}
                className={isCritical ? "fill-destructive" : undefined}
                style={{
                  fill: isCritical ? undefined : (taskColor ?? "var(--foreground)"),
                  fillOpacity: 0.5,
                  pointerEvents: "none",
                  stroke: "hsl(var(--ring))",
                  strokeWidth: 1.5,
                }}
              />
            )}
            {/* Dependency drag target highlight */}
            {depDragState?.targetTaskId === task.id && (
              <rect
                x={x - 3}
                y={barY - 3}
                width={barWidth + 6}
                height={config.barHeight + 6}
                rx={config.barRadius + 2}
                ry={config.barRadius + 2}
                fill="none"
                className="stroke-primary"
                strokeWidth={2}
                strokeDasharray="4 2"
                style={{ pointerEvents: "none" }}
              />
            )}
          </Fragment>
        );
      })}

      {/* Dependency drag preview line */}
      {depDragState && (
        <line
          x1={depDragState.fromX}
          y1={depDragState.fromY}
          x2={depDragState.currentX}
          y2={depDragState.currentY}
          className="stroke-primary"
          strokeWidth={2}
          strokeDasharray="6 3"
          style={{ pointerEvents: "none" }}
        />
      )}
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
  color,
  isHovered,
  depDragTargeted,
  onClick,
  onDoubleClick,
  onMouseEnter,
  onMouseLeave,
  onContextMenu,
  onConnectorDragStart,
}: {
  task: Task;
  y: number;
  config: GanttConfig;
  chartStartDate: Date;
  pxPerDay: number;
  isCritical: boolean;
  isSelected: boolean;
  color: string | null;
  isHovered: boolean;
  depDragTargeted: boolean;
  onClick: () => void;
  onDoubleClick: () => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
  onConnectorDragStart: (e: React.PointerEvent, sourceTaskId: string, sourceEdge: "start" | "finish", fromX: number, fromY: number) => void;
}) {
  const cx = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
  const cy = y + config.rowHeight / 2;
  const size = config.milestoneSize / 2;

  return (
    <g className="cursor-pointer" style={{ pointerEvents: "auto" }} onClick={onClick} onDoubleClick={onDoubleClick} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} onContextMenu={onContextMenu}>
      <rect
        x={cx - size}
        y={cy - size}
        width={config.milestoneSize}
        height={config.milestoneSize}
        rx={2}
        ry={2}
        transform={`rotate(45 ${cx} ${cy})`}
        className={isCritical ? "fill-destructive" : (!color ? "fill-foreground" : undefined)}
        style={!isCritical && color ? { fill: color } : undefined}
        stroke={isSelected ? "hsl(var(--ring))" : (!isCritical && !color ? "var(--border)" : "none")}
        strokeWidth={isSelected ? 2 : (!isCritical && !color ? 1.5 : 0)}
      />
      {depDragTargeted && (
        <circle
          cx={cx}
          cy={cy}
          r={size + 6}
          fill="none"
          className="stroke-primary"
          strokeWidth={2}
          strokeDasharray="4 2"
          style={{ pointerEvents: "none" }}
        />
      )}
      {isHovered && (
        <>
          <circle
            cx={cx - size - 8}
            cy={cy}
            r={5}
            className="fill-primary stroke-background"
            strokeWidth={1.5}
            style={{ cursor: "crosshair", pointerEvents: "auto" }}
            onPointerDown={(e) => { e.stopPropagation(); onConnectorDragStart(e, task.id, "start", cx - size - 8, cy); }}
          />
          <circle
            cx={cx + size + 8}
            cy={cy}
            r={5}
            className="fill-primary stroke-background"
            strokeWidth={1.5}
            style={{ cursor: "crosshair", pointerEvents: "auto" }}
            onPointerDown={(e) => { e.stopPropagation(); onConnectorDragStart(e, task.id, "finish", cx + size + 8, cy); }}
          />
        </>
      )}
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
  color,
  onClick,
  onDoubleClick,
  onMouseEnter,
  onMouseLeave,
  onContextMenu,
}: {
  task: Task;
  y: number;
  config: GanttConfig;
  chartStartDate: Date;
  pxPerDay: number;
  isCritical: boolean;
  isSelected: boolean;
  color: string | null;
  onClick: () => void;
  onDoubleClick: () => void;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}) {
  const x = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
  const barWidth = taskSpanWidthPx(
    new Date(task.start_date),
    new Date(task.finish_date),
    pxPerDay,
  );
  const cy = y + config.rowHeight / 2;
  const h = 12;
  const tri = 6;
  const r = 2;
  const top = cy - h / 2;
  const bot = cy + h / 2;
  const right = x + barWidth;

  // Single path: rounded top-left → rounded top-right → right triangle → bar bottom → left triangle
  const d = [
    `M ${x + r},${top}`,
    `H ${right - r}`,
    `Q ${right},${top} ${right},${top + r}`,
    `V ${bot}`,
    `L ${right},${bot + tri}`,
    `L ${right - tri},${bot}`,
    `H ${x + tri}`,
    `L ${x},${bot + tri}`,
    `L ${x},${bot}`,
    `V ${top + r}`,
    `Q ${x},${top} ${x + r},${top}`,
    "Z",
  ].join(" ");

  const fillStyle = isCritical
    ? undefined
    : color
      ? { fill: color, fillOpacity: 0.45 }
      : { fill: "transparent", stroke: "var(--border)", strokeWidth: 1.5 };
  const fillClass = isCritical ? "fill-destructive" : undefined;

  return (
    <g className="cursor-pointer" style={{ pointerEvents: "auto" }} onClick={onClick} onDoubleClick={onDoubleClick} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} onContextMenu={onContextMenu}>
      <path
        d={d}
        className={fillClass}
        style={fillStyle}
        stroke={isSelected ? "hsl(var(--ring))" : undefined}
        strokeWidth={isSelected ? 2 : undefined}
      />
    </g>
  );
}
