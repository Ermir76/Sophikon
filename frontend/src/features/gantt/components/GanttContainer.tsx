import { useRef, useLayoutEffect, useMemo, useCallback } from "react";
import type { Task, Dependency } from "@/features/tasks/types";
import type { GanttConfig, ZoomLevel } from "../types";
import { differenceInCalendarDays } from "../utils/dateUtils";
import { GanttTable, GanttTableHeader } from "./GanttTable";
import { GanttChart } from "./GanttChart";
import { GanttHoverTooltip } from "./GanttHoverTooltip";
import { TimelineHeader } from "./TimelineHeader";
import { GanttClickPopoverOverlay } from "./GanttClickPopoverOverlay";
import { useGanttInteractions } from "../hooks/useGanttInteractions";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/shared/ui/resizable";

interface GanttContainerProps {
  tasks: Task[];
  dependencies: Dependency[];
  config: GanttConfig;
  zoom: ZoomLevel;
  pxPerDay: number;
  showCriticalPath: boolean;
  selectedTaskId: string | null;
  onTaskClick: (taskId: string) => void;
  collapsedIds: Set<string>;
  onToggleCollapse: (taskId: string) => void;
  chartStartDate: Date;
  chartEndDate: Date;
  onContainerResize: (width: number) => void;
  onZoomAtPoint: (deltaY: number, cursorX: number) => void;
  chartScrollRef: React.RefObject<{
    scrollTo: (left: number) => void;
  } | null>;
  colorMap?: Map<string, string | null>;
}

export function GanttContainer({
  tasks,
  dependencies,
  config,
  zoom,
  pxPerDay,
  showCriticalPath,
  selectedTaskId,
  onTaskClick,
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
    clickedTaskId,
    setClickedTaskId,
    handleTaskHover,
    handleChartTaskClick,
    handleChartWheel,
  } = useGanttInteractions({
    onTaskClick,
    onZoomAtPoint,
    chartBodyRef: timelineRef,
  });

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
  useLayoutEffect(() => {
    if (chartScrollRef) {
      (chartScrollRef as React.RefObject<{ scrollTo: (left: number) => void } | null>).current = {
        scrollTo: (left: number) => {
          if (timelineRef.current) {
            timelineRef.current.scrollLeft = left;
          }
        },
      };
    }
  });

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
      direction="horizontal"
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
              className="h-full overflow-auto relative"
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
                onTaskHover={handleTaskHover}
                chartStartDate={chartStartDate}
                chartEndDate={chartEndDate}
                totalWidth={totalWidth}
                colorMap={colorMap}
              />

              {/* Hover tooltip overlay */}
              {hoveredTaskId && hoveredTaskId !== clickedTaskId && (
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
                clickedTaskId={clickedTaskId}
                taskMap={taskMap}
                chartStartDate={chartStartDate}
                pxPerDay={pxPerDay}
                config={config}
                chartBodyRef={timelineRef}
                onClose={() => setClickedTaskId(null)}
              />
            </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
