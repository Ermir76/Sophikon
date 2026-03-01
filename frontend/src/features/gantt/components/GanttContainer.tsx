import { useRef, useCallback, useLayoutEffect, useState } from "react";
import type { Task, Dependency } from "@/features/tasks/types";
import type { GanttConfig, ZoomLevel } from "../types";
import { differenceInCalendarDays } from "../utils/dateUtils";
import { GanttTable } from "./GanttTable";
import { GanttChart } from "./GanttChart";
import { TimelineHeader } from "./TimelineHeader";

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
}: GanttContainerProps) {
  const tableScrollRef = useRef<HTMLDivElement>(null);
  const chartBodyRef = useRef<HTMLDivElement>(null);
  const timelineHeaderRef = useRef<HTMLDivElement>(null);
  const rightPanelRef = useRef<HTMLDivElement>(null);
  const isSyncing = useRef(false);
  const [containerReady, setContainerReady] = useState(false);

  const totalDays = differenceInCalendarDays(chartEndDate, chartStartDate);
  const totalWidth = totalDays * pxPerDay;

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

  return (
    <div className="flex flex-1 overflow-hidden border border-border rounded-md min-w-0 min-h-0">
      {/* Left: Task Table */}
      <div className="w-[280px] sm:w-[480px] shrink-0 border-r border-border">
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

      {/* Right: Timeline Header + Chart Body */}
      <div ref={rightPanelRef} className="flex flex-col flex-1 min-w-0 h-full">
        {containerReady && (
          <>
            {/* Timeline header — pinned at top, scrollLeft synced */}
            <div
              ref={timelineHeaderRef}
              className="overflow-hidden flex-shrink-0"
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

            {/* Chart body — overflow auto, scroll synced */}
            <div
              ref={chartBodyRef}
              className="flex-1 overflow-auto"
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
                onTaskClick={onTaskClick}
                chartStartDate={chartStartDate}
                chartEndDate={chartEndDate}
                totalWidth={totalWidth}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
