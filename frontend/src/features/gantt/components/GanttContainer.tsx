import { useRef, useLayoutEffect, useState, useMemo } from "react";
import type { Task, Dependency } from "@/features/tasks/types";
import type { GanttConfig, ZoomLevel } from "../types";
import { differenceInCalendarDays } from "../utils/dateUtils";
import { GanttTable, GanttTableHeader } from "./GanttTable";
import { GanttChart } from "./GanttChart";
import { GanttHoverTooltip } from "./GanttHoverTooltip";
import { TimelineHeader } from "./TimelineHeader";
import { GanttClickPopoverOverlay } from "./GanttClickPopoverOverlay";
import { useGanttScrollSync } from "../hooks/useGanttScrollSync";
import { useGanttInteractions } from "../hooks/useGanttInteractions";

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
  const {
    tableScrollRef,
    chartBodyRef,
    timelineHeaderRef,
    topScrollRef,
    handleChartBodyScroll,
    handleTableScroll,
    handleTopScroll,
  } = useGanttScrollSync();
  const rightPanelRef = useRef<HTMLDivElement>(null);
  const [containerReady, setContainerReady] = useState(false);
  const [containerWidth, setContainerWidth] = useState(0);

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
    chartBodyRef,
  });

  const taskMap = useMemo(() => {
    const map = new Map<string, { task: Task; index: number }>();
    tasks.forEach((t, i) => map.set(t.id, { task: t, index: i }));
    return map;
  }, [tasks]);

  const totalDays = differenceInCalendarDays(chartEndDate, chartStartDate);
  const chartWidth = totalDays * pxPerDay;
  const totalWidth = Math.max(chartWidth, containerWidth);

  // Expose scrollTo to parent via ref
  useLayoutEffect(() => {
    if (chartScrollRef) {
      (chartScrollRef as React.RefObject<{ scrollTo: (left: number) => void } | null>).current = {
        scrollTo: (left: number) => {
          if (chartBodyRef.current) {
            chartBodyRef.current.scrollLeft = left;
          }
        },
      };
    }
  });

  // Track right panel width via ResizeObserver
  useLayoutEffect(() => {
    const el = rightPanelRef.current;
    if (!el) return;

    const update = (w: number) => {
      onContainerResize(w);
      setContainerWidth(w);
      setContainerReady(true);
    };

    update(Math.round(el.clientWidth));

    const observer = new ResizeObserver(([entry]) => {
      update(Math.round(entry.contentRect.width));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [onContainerResize]);





  const headerRowHeight = config.headerHeight + 12;

  return (
    <div
      className="grid overflow-hidden border border-border rounded-md min-w-0 min-h-0 grid-cols-[280px_1fr] sm:grid-cols-[480px_1fr]"
      style={{
        gridTemplateRows: `${headerRowHeight}px auto`,
      }}
    >
      {/* Table header — col 1, row 1 */}
      <div className="border-r border-b border-border min-w-0">
        <GanttTableHeader />
      </div>

      {/* Chart header area — col 2, row 1 */}
      <div className="flex flex-col min-w-0 border-b border-border">
        {containerReady && (
          <>
            {/* Timeline header */}
            <div
              ref={timelineHeaderRef}
              className="overflow-hidden"
              style={{ height: config.headerHeight }}
            >
              <TimelineHeader
                chartStartDate={chartStartDate}
                chartEndDate={chartEndDate}
                zoom={zoom}
                pxPerDay={pxPerDay}
                totalWidth={totalWidth}
                headerHeight={config.headerHeight}
              />
            </div>

            {/* Top horizontal scrollbar */}
            <div
              ref={topScrollRef}
              className="overflow-x-auto overflow-y-hidden"
              style={{ height: 12 }}
              onScroll={handleTopScroll}
            >
              <div style={{ width: totalWidth, height: 1 }} />
            </div>
          </>
        )}
      </div>

      {/* Table body — col 1, row 2 */}
      <div className="border-r border-border min-h-0 min-w-0">
        <GanttTable
          tasks={tasks}
          config={config}
          selectedTaskId={selectedTaskId}
          onTaskClick={onTaskClick}
          collapsedIds={collapsedIds}
          onToggleCollapse={onToggleCollapse}
          scrollRef={tableScrollRef}
          onScroll={handleTableScroll}
        />
      </div>

      {/* Chart body — col 2, row 2 */}
      <div ref={rightPanelRef} className="min-h-0 min-w-0">
        {containerReady && (
          <div
            ref={chartBodyRef}
            className="overflow-auto relative"
            style={{ lineHeight: 0 }}
            onScroll={handleChartBodyScroll}
            onWheel={handleChartWheel}
          >
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
              chartBodyRef={chartBodyRef}
              onClose={() => setClickedTaskId(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
