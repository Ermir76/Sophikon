import { useRef, useLayoutEffect, useImperativeHandle, useMemo, useCallback, useState } from "react";
import type { Task, Dependency } from "@/features/tasks";
import type { GanttConfig, ZoomLevel } from "../types";
import { differenceInCalendarDays } from "../utils/dateUtils";
import { GanttTable, GanttTableHeader } from "./GanttTable";
import { GanttChart } from "./GanttChart";
import { GanttHoverTooltip } from "./GanttHoverTooltip";
import { TimelineHeader } from "./TimelineHeader";
import { GanttClickPopoverOverlay } from "./GanttClickPopoverOverlay";
import { useGanttInteractions } from "../hooks/useGanttInteractions";
import { useGanttBarDrag } from "../hooks/useGanttBarDrag";
import { GanttContextMenu } from "./GanttContextMenu";
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

  const { dragState, startDrag } = useGanttBarDrag({ pxPerDay, projectId });

  const [contextMenuState, setContextMenuState] = useState<{
    taskId: string;
    x: number;
    y: number;
  } | null>(null);

  const handleTaskContextMenu = useCallback((e: React.MouseEvent, taskId: string) => {
    setContextMenuState({ taskId, x: e.clientX, y: e.clientY });
  }, []);

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
          />

          {/* Hover tooltip overlay */}
          {hoveredTaskId && hoveredTaskId !== selectedTaskId && (
            <GanttHoverTooltip
              hoveredTaskId={hoveredTaskId}
              taskMap={taskMap}
              chartStartDate={chartStartDate}
              pxPerDay={pxPerDay}
              config={config}
            />
          )}

          {/* Click popover overlay */}
          <GanttClickPopoverOverlay
            clickedTaskId={selectedTaskId}
            taskMap={taskMap}
            chartStartDate={chartStartDate}
            pxPerDay={pxPerDay}
            config={config}
            onClose={() => {
              if (selectedTaskId) {
                onTaskClick(selectedTaskId);
              }
            }}
          />

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
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
