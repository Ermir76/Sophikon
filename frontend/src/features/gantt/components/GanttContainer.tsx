import { useRef, useCallback, useLayoutEffect, useState, useMemo } from "react";
import type { Task, Dependency } from "@/features/tasks/types";
import type { GanttConfig, ZoomLevel } from "../types";
import { differenceInCalendarDays, dateToX, format } from "../utils/dateUtils";
import { GanttTable, GanttTableHeader } from "./GanttTable";
import { GanttChart } from "./GanttChart";
import { TimelineHeader } from "./TimelineHeader";
import { GanttBarPopover } from "./GanttBarPopover";

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
  const tableScrollRef = useRef<HTMLDivElement>(null);
  const chartBodyRef = useRef<HTMLDivElement>(null);
  const timelineHeaderRef = useRef<HTMLDivElement>(null);
  const topScrollRef = useRef<HTMLDivElement>(null);
  const rightPanelRef = useRef<HTMLDivElement>(null);
  const isSyncing = useRef(false);
  const [containerReady, setContainerReady] = useState(false);
  const [containerWidth, setContainerWidth] = useState(0);
  const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);
  const [clickedTaskId, setClickedTaskId] = useState<string | null>(null);

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

  // Sync: chart body scroll → table scrollTop + header scrollLeft
  const handleChartBodyScroll = useCallback(() => {
    if (isSyncing.current) return;
    isSyncing.current = true;

    const cb = chartBodyRef.current;
    if (cb) {
      if (tableScrollRef.current) {
        tableScrollRef.current.scrollTop = cb.scrollTop;
      }
      if (timelineHeaderRef.current) {
        timelineHeaderRef.current.scrollLeft = cb.scrollLeft;
      }
      if (topScrollRef.current) {
        topScrollRef.current.scrollLeft = cb.scrollLeft;
      }
    }

    requestAnimationFrame(() => {
      isSyncing.current = false;
    });
  }, []);

  // Sync: table scroll → chart body scrollTop
  const handleTableScroll = useCallback(() => {
    if (isSyncing.current) return;
    isSyncing.current = true;

    if (tableScrollRef.current && chartBodyRef.current) {
      chartBodyRef.current.scrollTop = tableScrollRef.current.scrollTop;
    }

    requestAnimationFrame(() => {
      isSyncing.current = false;
    });
  }, []);

  const handleTopScroll = useCallback(() => {
    if (isSyncing.current) return;
    isSyncing.current = true;

    if (topScrollRef.current && chartBodyRef.current) {
      chartBodyRef.current.scrollLeft = topScrollRef.current.scrollLeft;
      if (timelineHeaderRef.current) {
        timelineHeaderRef.current.scrollLeft = topScrollRef.current.scrollLeft;
      }
    }

    requestAnimationFrame(() => {
      isSyncing.current = false;
    });
  }, []);

  const handleTaskHover = useCallback((taskId: string | null) => {
    setHoveredTaskId(taskId);
  }, []);

  const handleChartTaskClick = useCallback(
    (taskId: string) => {
      setClickedTaskId((prev) => (prev === taskId ? null : taskId));
      onTaskClick(taskId);
    },
    [onTaskClick],
  );

  // Wheel handler on chart body wrapper
  const handleChartWheel = useCallback(
    (e: React.WheelEvent<HTMLDivElement>) => {
      e.preventDefault();

      if (e.ctrlKey || e.metaKey) {
        // Zoom at cursor
        const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
        const cursorX = e.clientX - rect.left + (chartBodyRef.current?.scrollLeft ?? 0);
        onZoomAtPoint(e.deltaY, cursorX);
        return;
      }

      const cb = chartBodyRef.current;
      if (!cb) return;

      if (e.shiftKey) {
        cb.scrollLeft += e.deltaY;
      } else {
        cb.scrollTop += e.deltaY;
        cb.scrollLeft += e.deltaX;
      }
    },
    [onZoomAtPoint],
  );

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
            {hoveredTaskId && hoveredTaskId !== clickedTaskId && (() => {
              const entry = taskMap.get(hoveredTaskId);
              if (!entry) return null;
              const { task, index } = entry;
              const barX = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
              const barY = index * config.rowHeight + config.rowHeight / 2;
              return (
                <div
                  className="absolute z-40 rounded-md bg-foreground text-background px-2.5 py-1.5 text-xs pointer-events-none shadow-md"
                  style={{
                    left: barX + 12,
                    top: barY + 12,
                    maxWidth: 240,
                  }}
                >
                  <div className="font-medium">{task.name}</div>
                  <div className="opacity-80 text-[10px]">
                    {format(new Date(task.start_date), "MM/dd")} – {format(new Date(task.finish_date), "MM/dd")} · {task.duration}m · {task.percent_complete}%
                  </div>
                </div>
              );
            })()}

            {/* Click popover overlay */}
            {clickedTaskId && (() => {
              const entry = taskMap.get(clickedTaskId);
              if (!entry) return null;
              const { task, index } = entry;
              const barX = dateToX(new Date(task.start_date), chartStartDate, pxPerDay);
              const barY = index * config.rowHeight + config.rowHeight;
              const containerEl = chartBodyRef.current;
              const popoverContainerWidth = containerEl?.scrollWidth ?? 800;
              const popoverContainerHeight = containerEl?.scrollHeight ?? 600;
              return (
                <GanttBarPopover
                  task={task}
                  x={barX}
                  y={barY}
                  containerWidth={popoverContainerWidth}
                  containerHeight={popoverContainerHeight}
                  onClose={() => setClickedTaskId(null)}
                />
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
