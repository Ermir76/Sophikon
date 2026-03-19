import { useRef, useLayoutEffect, useImperativeHandle, useMemo, useCallback, useState } from "react";
import { MoreHorizontal } from "lucide-react";
import type { Task, Dependency } from "@/features/tasks";
import { useDeleteDependency } from "@/features/tasks";
import type { GanttConfig, ZoomLevel } from "../types";
import { differenceInCalendarDays, dateToX, taskSpanWidthPx } from "../utils/dateUtils";
import { GanttTable, GanttTableHeader } from "./GanttTable";
import { GanttChart } from "./GanttChart";
import { GanttHoverTooltip } from "./GanttHoverTooltip";
import { TimelineHeader } from "./TimelineHeader";
import { useGanttInteractions } from "../hooks/useGanttInteractions";
import { useGanttBarDrag } from "../hooks/useGanttBarDrag";
import { useGanttDependencyDrag } from "../hooks/useGanttDependencyDrag";
import { GanttContextMenu } from "./GanttContextMenu";
import { GanttBarQuickInfo } from "./GanttBarQuickInfo";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/shared/ui/resizable";

interface GanttContainerProps {
  projectId: string;
  tasks: Task[];
  dependencies: Dependency[];
  config: GanttConfig;
  zoom: ZoomLevel;
  pxPerDay: number;
  showCriticalPath: boolean;
  selectedTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  onTaskDoubleClick: (taskId: string) => void;
  collapsedIds: Set<string>;
  onToggleCollapse: (taskId: string) => void;
  chartStartDate: Date;
  chartEndDate: Date;
  onContainerResize: (width: number) => void;
  onZoomAtPoint: (deltaY: number, cursorX: number) => void;
  chartScrollRef: React.Ref<{
    scrollTo: (left: number) => void;
  }>;
  colorMap?: Map<string, string | null>;
}

export function GanttContainer({
  projectId,
  tasks,
  dependencies,
  config,
  zoom,
  pxPerDay,
  showCriticalPath,
  selectedTaskId,
  onTaskClick,
  onTaskDoubleClick,
  collapsedIds,
  onToggleCollapse,
  chartStartDate,
  chartEndDate,
  onContainerResize,
  onZoomAtPoint,
  chartScrollRef,
  colorMap,
}: GanttContainerProps) {
  const tableRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const containerWidthRef = useRef(0);

  const {
    hoveredTaskId,
    handleTaskHover,
    handleChartTaskClick,
    handleChartTaskDoubleClick,
    handleChartWheel,
  } = useGanttInteractions({
    onTaskClick,
    onTaskDoubleClick,
    onZoomAtPoint,
    chartBodyRef: timelineRef,
  });

  const { dragState, startDrag } = useGanttBarDrag({ pxPerDay, projectId, onTaskClick });

  const { depDragState, startConnectorDrag } = useGanttDependencyDrag({
    projectId,
    tasks,
    rowHeight: config.rowHeight,
    headerHeight: config.headerHeight,
    getTimelineEl: () => timelineRef.current,
  });

  const [contextMenuState, setContextMenuState] = useState<{
    taskId: string;
    x: number;
    y: number;
  } | null>(null);

  const handleTaskContextMenu = useCallback((e: React.MouseEvent, taskId: string) => {
    setContextMenuState({ taskId, x: e.clientX, y: e.clientY });
  }, []);

  const [depContextMenuState, setDepContextMenuState] = useState<{
    depId: string;
    x: number;
    y: number;
  } | null>(null);

  const [quickInfoState, setQuickInfoState] = useState<{
    taskId: string;
    x: number;
    y: number;
  } | null>(null);

  const handleDependencyContextMenu = useCallback((e: React.MouseEvent, depId: string) => {
    setDepContextMenuState({ depId, x: e.clientX, y: e.clientY });
  }, []);

  const deleteDependency = useDeleteDependency(projectId);

  const taskMap = useMemo(() => {
    const map = new Map<string, { task: Task; index: number }>();
    tasks.forEach((t, i) => map.set(t.id, { task: t, index: i }));
    return map;
  }, [tasks]);

  const totalDays = differenceInCalendarDays(chartEndDate, chartStartDate);
  const chartWidth = totalDays * pxPerDay;
  const totalWidth = Math.max(chartWidth, containerWidthRef.current);

  // Inline vertical scroll sync
  const handleScroll = useCallback((source: "table" | "timeline") => {
    const from = source === "table" ? tableRef.current : timelineRef.current;
    const to = source === "table" ? timelineRef.current : tableRef.current;
    if (from && to && to.scrollTop !== from.scrollTop) {
      to.scrollTop = from.scrollTop;
    }
  }, []);

  // Expose scrollTo to parent via ref
  useImperativeHandle(chartScrollRef, () => ({
    scrollTo: (left: number) => {
      if (timelineRef.current) {
        timelineRef.current.scrollLeft = left;
      }
    },
  }), []);

  // Track right panel width via ResizeObserver
  useLayoutEffect(() => {
    const el = timelineRef.current;
    if (!el) return;

    const update = (w: number) => {
      onContainerResize(w);
      containerWidthRef.current = w;
    };

    update(Math.round(el.clientWidth));

    const observer = new ResizeObserver(([entry]) => {
      update(Math.round(entry.contentRect.width));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [onContainerResize]);

  return (
    <ResizablePanelGroup
      orientation="horizontal"
      className="h-full overflow-hidden border border-border rounded-md"
    >
      {/* Left panel: table header + rows */}
      <ResizablePanel defaultSize="30%" minSize="15%" maxSize="50%">
        <div className="h-full overflow-auto" ref={tableRef} onScroll={() => handleScroll("table")}>
          <div className="sticky top-0 z-10 border-b border-border" style={{ height: config.headerHeight }}>
            <GanttTableHeader />
          </div>
          <GanttTable
            tasks={tasks}
            config={config}
            selectedTaskId={selectedTaskId}
            onTaskClick={onTaskClick}
            collapsedIds={collapsedIds}
            onToggleCollapse={onToggleCollapse}
          />
        </div>
      </ResizablePanel>

      <ResizableHandle withHandle />

      {/* Right panel: timeline header + chart */}
      <ResizablePanel defaultSize="70%">
        <div
          ref={timelineRef}
          className={`h-full overflow-auto relative${dragState ? " cursor-grabbing" : ""}`}
          style={{ lineHeight: 0 }}
          onScroll={() => handleScroll("timeline")}
          onWheel={handleChartWheel}
        >
          <div className="sticky top-0 z-10">
            <TimelineHeader
              chartStartDate={chartStartDate}
              chartEndDate={chartEndDate}
              zoom={zoom}
              pxPerDay={pxPerDay}
              totalWidth={totalWidth}
              headerHeight={config.headerHeight}
            />
          </div>

          <GanttChart
            tasks={tasks}
            dependencies={dependencies}
            config={config}
            pxPerDay={pxPerDay}
            showCriticalPath={showCriticalPath}
            selectedTaskId={selectedTaskId}
            hoveredTaskId={hoveredTaskId}
            onTaskClick={handleChartTaskClick}
            onTaskDoubleClick={handleChartTaskDoubleClick}
            onTaskHover={handleTaskHover}
            chartStartDate={chartStartDate}
            chartEndDate={chartEndDate}
            totalWidth={totalWidth}
            colorMap={colorMap}
            dragState={dragState}
            onBarDragStart={startDrag}
            onTaskContextMenu={handleTaskContextMenu}
            depDragState={depDragState}
            onConnectorDragStart={startConnectorDrag}
            onDependencyContextMenu={handleDependencyContextMenu}
          />

          {/* Open detail button — shown on bar hover */}
          {hoveredTaskId && !depDragState && !dragState && (() => {
            const entry = taskMap.get(hoveredTaskId);
            if (!entry || entry.task.is_summary) return null;
            const { task, index } = entry;
            const barX = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
            const barWidth = taskSpanWidthPx(new Date(task.start_date), new Date(task.finish_date), pxPerDay);
            if (barWidth < 24) return null;
            const barY = index * config.rowHeight + (config.rowHeight - config.barHeight) / 2;
            return (
              <button
                className="absolute z-20 flex items-center justify-center rounded bg-black/20 hover:bg-black/40 transition-colors"
                style={{
                  left: barX + barWidth - 28,
                  top: config.headerHeight + barY + (config.barHeight / 2) - 12,
                  width: 24,
                  height: 24,
                  cursor: "pointer",
                }}
                onMouseEnter={() => handleTaskHover(hoveredTaskId)}
                onMouseLeave={() => handleTaskHover(null)}
                onClick={(e) => { e.stopPropagation(); setQuickInfoState({ taskId: hoveredTaskId, x: e.clientX, y: e.clientY }); }}
              >
                <MoreHorizontal className="size-3.5 text-white" />
              </button>
            );
          })()}

          {/* Dependency arrow context menu */}
          {depContextMenuState && (
            <>
              <div
                className="fixed inset-0 z-40"
                onPointerDown={() => setDepContextMenuState(null)}
              />
              <div
                className="fixed z-50 min-w-[140px] rounded-md border border-border bg-popover shadow-md py-1"
                style={{ left: depContextMenuState.x, top: depContextMenuState.y }}
              >
                <button
                  className="w-full text-left px-3 py-1.5 text-sm text-destructive hover:bg-muted"
                  onClick={() => {
                    deleteDependency.mutate(depContextMenuState.depId);
                    setDepContextMenuState(null);
                  }}
                >
                  Delete dependency
                </button>
              </div>
            </>
          )}

          {/* Context menu */}
          {contextMenuState && (() => {
            const entry = taskMap.get(contextMenuState.taskId);
            if (!entry) return null;
            return (
              <GanttContextMenu
                task={entry.task}
                projectId={projectId}
                x={contextMenuState.x}
                y={contextMenuState.y}
                onClose={() => setContextMenuState(null)}
                onOpenDetails={onTaskDoubleClick}
              />
            );
          })()}

          {/* Quick info popover (⋯ button) */}
          {quickInfoState && (() => {
            const entry = taskMap.get(quickInfoState.taskId);
            if (!entry) return null;
            return (
              <GanttBarQuickInfo
                task={entry.task}
                projectId={projectId}
                x={quickInfoState.x}
                y={quickInfoState.y}
                onClose={() => setQuickInfoState(null)}
                onOpenDetails={(id) => { onTaskDoubleClick(id); setQuickInfoState(null); }}
              />
            );
          })()}
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
