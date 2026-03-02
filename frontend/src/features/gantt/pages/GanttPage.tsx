import { useState, useRef, useCallback, useMemo } from "react";
import { useParams } from "react-router";
import { Loader2, BarChart3 } from "lucide-react";
import { useTasks } from "@/features/tasks/hooks/useTasks";
import { useDependencies } from "@/features/tasks/hooks/useDependencies";
import { useProject } from "@/features/projects/hooks/useProjects";
import { useCollapsedTree } from "@/shared/hooks/useCollapsedTree";
import { buildColorInheritanceMap } from "../utils/colorInheritance";
import { QueryError } from "@/shared/components/QueryError";
import type { Task } from "@/features/tasks/types";
import type { ZoomLevel } from "../types";
import { DEFAULT_GANTT_CONFIG, ZOOM_PX_PER_DAY } from "../types";
import { getProjectDateRange, dateToX, differenceInCalendarDays } from "../utils/dateUtils";
import { GanttToolbar } from "../components/GanttToolbar";
import { GanttContainer } from "../components/GanttContainer";

const EMPTY_TASKS: Task[] = [];
const getParentId = (t: Task) => t.parent_task_id;
const ZOOM_WHEEL_FACTOR = 0.002;

export default function GanttPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: taskData, isLoading: tasksLoading, error: tasksError } = useTasks(projectId);
  const { data: depData, isLoading: depsLoading, error: depsError } = useDependencies(projectId);
  const { data: project } = useProject(projectId ?? "");

  const [zoom, setZoom] = useState<ZoomLevel>("week");
  const [customPxPerDay, setCustomPxPerDay] = useState<number | null>(null);
  const [showCriticalPath, setShowCriticalPath] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const containerWidthRef = useRef(0);
  const chartScrollRef = useRef<{ scrollTo: (left: number) => void } | null>(null);

  const tasks = taskData?.items ?? EMPTY_TASKS;
  const dependencies = depData?.items ?? [];

  const { visibleData: visibleTasks, collapsedIds, toggleCollapse } =
    useCollapsedTree(`sophikon:gantt_collapsed:${projectId}`, tasks, getParentId);

  const pxPerDay = customPxPerDay ?? ZOOM_PX_PER_DAY[zoom];

  const { start: chartStartDate, end: chartEndDate } = useMemo(
    () => getProjectDateRange(tasks),
    [tasks],
  );

  const totalDays = differenceInCalendarDays(chartEndDate, chartStartDate);
  const config = DEFAULT_GANTT_CONFIG;

  const colorMap = useMemo(
    () => buildColorInheritanceMap(tasks, project?.color ?? null),
    [tasks, project?.color],
  );

  const handleContainerResize = useCallback((width: number) => {
    containerWidthRef.current = width;
  }, []);

  const handleZoomAtPoint = useCallback(
    (deltaY: number, cursorX: number) => {
      const zoomDelta = -deltaY * ZOOM_WHEEL_FACTOR;
      const factor = Math.pow(2, zoomDelta);
      const newPxPerDay = Math.max(1, Math.min(80, pxPerDay * factor));

      // Recenter on cursor position
      const newCursorX = cursorX * (newPxPerDay / pxPerDay);
      const rect = containerWidthRef.current;
      const scrollFraction = rect > 0 ? (cursorX - (chartScrollRef.current ? 0 : 0)) / rect : 0;
      const newScrollLeft = newCursorX - scrollFraction * rect;

      let newZoom: ZoomLevel;
      if (newPxPerDay >= 25) {
        newZoom = "day";
      } else if (newPxPerDay >= 8) {
        newZoom = "week";
      } else {
        newZoom = "month";
      }

      setZoom(newZoom);
      setCustomPxPerDay(newPxPerDay);

      // Schedule scroll after re-render
      requestAnimationFrame(() => {
        chartScrollRef.current?.scrollTo(Math.max(0, newScrollLeft));
      });
    },
    [pxPerDay],
  );

  const handleZoomChange = useCallback((newZoom: ZoomLevel) => {
    setZoom(newZoom);
    setCustomPxPerDay(null);
  }, []);

  const handleScrollToToday = useCallback(() => {
    const cw = containerWidthRef.current;
    const todayX = dateToX(new Date(), chartStartDate, pxPerDay);
    chartScrollRef.current?.scrollTo(Math.max(0, todayX - cw / 3));
  }, [pxPerDay, chartStartDate]);

  const handleZoomToFit = useCallback(() => {
    const cw = containerWidthRef.current;
    if (tasks.length === 0 || cw === 0 || totalDays <= 0) return;

    const fitted = cw / totalDays;

    if (fitted >= 25) {
      setZoom("day");
    } else if (fitted >= 8) {
      setZoom("week");
    } else {
      setZoom("month");
    }

    setCustomPxPerDay(fitted);

    requestAnimationFrame(() => {
      chartScrollRef.current?.scrollTo(0);
    });
  }, [tasks.length, totalDays]);

  const handleTaskClick = useCallback((taskId: string) => {
    setSelectedTaskId((prev) => (prev === taskId ? null : taskId));
  }, []);

  const isLoading = tasksLoading || depsLoading;
  const error = tasksError || depsError;

  if (error) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-4">
        <QueryError message="Failed to load Gantt chart data." />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-muted-foreground">
        <BarChart3 className="size-12" />
        <p className="text-lg font-medium">No tasks to display</p>
        <p className="text-sm">Add tasks to your project to see them on the Gantt chart.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-2 p-4 overflow-hidden min-w-0 min-h-0">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Gantt Chart</h1>
        <GanttToolbar
          zoom={zoom}
          onZoomChange={handleZoomChange}
          showCriticalPath={showCriticalPath}
          onToggleCriticalPath={() => setShowCriticalPath((v) => !v)}
          onScrollToToday={handleScrollToToday}
          onZoomToFit={handleZoomToFit}
        />
      </div>

      <div className="flex-1 min-h-0">
        <GanttContainer
          tasks={visibleTasks}
          dependencies={dependencies}
          config={config}
          zoom={zoom}
          pxPerDay={pxPerDay}
          showCriticalPath={showCriticalPath}
          selectedTaskId={selectedTaskId}
          onTaskClick={handleTaskClick}
          collapsedIds={collapsedIds}
          onToggleCollapse={toggleCollapse}
          chartStartDate={chartStartDate}
          chartEndDate={chartEndDate}
          onContainerResize={handleContainerResize}
          onZoomAtPoint={handleZoomAtPoint}
          chartScrollRef={chartScrollRef}
          colorMap={colorMap}
        />
      </div>
    </div>
  );
}
