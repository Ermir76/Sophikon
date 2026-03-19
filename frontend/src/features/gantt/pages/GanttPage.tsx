import { useState, useRef, useCallback, useMemo } from "react";
import { useParams } from "react-router";
import { BarChart3 } from "lucide-react";
import { toast } from "sonner";
import { useTasks, useDependencies, TaskDetailPanel, type Task } from "@/features/tasks";
import { useProject, useUpdateProject } from "@/features/projects";
import { useCollapsedTree } from "@/shared/hooks/useCollapsedTree";
import { buildColorInheritanceMap } from "../utils/colorInheritance";
import { QueryError } from "@/shared/components/QueryError";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageEmpty } from "@/shared/components/state/PageEmpty";
import type { ZoomLevel } from "../types";
import { DEFAULT_GANTT_CONFIG, ZOOM_PX_PER_DAY } from "../types";
import { getProjectDateRange, dateToX, differenceInCalendarDays } from "../utils/dateUtils";
import { GanttToolbar } from "../components/GanttToolbar";
import { GanttContainer } from "../components/GanttContainer";
import { useCalculateSchedule } from "../hooks/useSchedule";

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
  const [detailTaskId, setDetailTaskId] = useState<string | null>(null);

  const containerWidthRef = useRef(0);
  const chartScrollRef = useRef<{ scrollTo: (left: number) => void } | null>(null);

  const tasks = taskData?.items ?? EMPTY_TASKS;
  const dependencies = depData?.items ?? [];

  const { visibleData: visibleTasks, collapsedIds, toggleCollapse } =
    useCollapsedTree(`sophikon:gantt_collapsed:${projectId}`, tasks, getParentId, true);

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

  // Schedule hooks
  const calculateSchedule = useCalculateSchedule(projectId);
  const updateProject = useUpdateProject(projectId);
  const autoCalculate = project?.settings?.auto_calculate ?? true;

  const handleManualCalculate = async () => {
    try {
      const data = await calculateSchedule.mutateAsync();
      toast.success(`Schedule recalculated - ${data.tasks_updated} tasks updated`);
    } catch {
      toast.error("Failed to recalculate schedule");
    }
  };

  const handleToggleAutoCalculate = async () => {
    const newValue = !autoCalculate;
    try {
      await updateProject.mutateAsync({ settings: { auto_calculate: newValue } });
      toast.success(`Scheduling mode: ${newValue ? "Auto" : "Manual"}`);
    } catch {
      toast.error("Failed to update scheduling mode");
    }
  };

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
      <PageShell>
        <QueryError message="Failed to load Gantt chart data." />
      </PageShell>
    );
  }

  if (isLoading) {
    return <PageLoading />;
  }

  if (tasks.length === 0) {
    return (
      <PageShell>
        <PageEmpty
          icon={BarChart3}
          title="No tasks to display"
          description="Add tasks to your project to see them on the Gantt chart."
        />
      </PageShell>
    );
  }

  return (
    <PageShell className="flex-1 overflow-hidden min-w-0">
      <PageHeader
        title="Gantt Chart"
        description="Timeline view for sequencing, dependencies, and critical path."
        action={
          <GanttToolbar
            zoom={zoom}
            onZoomChange={handleZoomChange}
            showCriticalPath={showCriticalPath}
            onToggleCriticalPath={() => setShowCriticalPath((v) => !v)}
            criticalTaskCount={tasks.filter((t) => t.is_critical).length}
            onScrollToToday={handleScrollToToday}
            onZoomToFit={handleZoomToFit}
            autoCalculate={autoCalculate}
            onToggleAutoCalculate={handleToggleAutoCalculate}
            onManualCalculate={handleManualCalculate}
            isCalculating={calculateSchedule.isPending}
          />
        }
      />

      <div className="flex-1 min-h-0">
        <GanttContainer
          projectId={projectId ?? ""}
          tasks={visibleTasks}
          dependencies={dependencies}
          config={config}
          zoom={zoom}
          pxPerDay={pxPerDay}
          showCriticalPath={showCriticalPath}
          selectedTaskId={selectedTaskId}
          onTaskClick={handleTaskClick}
          onTaskDoubleClick={setDetailTaskId}
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

      <TaskDetailPanel
        projectId={projectId ?? ""}
        taskId={detailTaskId}
        isOpen={!!detailTaskId}
        onClose={() => setDetailTaskId(null)}
      />
    </PageShell>
  );
}
