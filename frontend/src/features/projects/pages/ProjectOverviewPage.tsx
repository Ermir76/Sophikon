import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import {
  AlertTriangle,
  CalendarDays,
  Coins,
  RefreshCcw,
  Route,
  Sparkles,
  Users,
} from "lucide-react";

import { useAiSuggestions } from "@/features/ai/hooks/useAi";
import { useProjectDashboard } from "@/features/projects/hooks/useProjectDashboard";
import { useProject } from "@/features/projects/hooks/useProjects";
import { QueryError } from "@/shared/components/QueryError";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageEmpty } from "@/shared/components/state/PageEmpty";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { getErrorMessage } from "@/shared/lib/errors";
import { useTimeWindowFilter } from "@/shared/hooks/useTimeWindowFilter";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { InsightsActivityCard } from "@/shared/ui/insights-activity-card";
import { InsightsMetricCard } from "@/shared/ui/insights-metric-card";
import { TimeWindowFilter } from "@/shared/ui/time-window-filter";

function severityClassName(severity: "LOW" | "MEDIUM" | "HIGH") {
  if (severity === "HIGH") {
    return "border-destructive/50 bg-destructive/15 text-destructive";
  }
  if (severity === "MEDIUM") {
    return "border-chart-3/50 bg-chart-3/15 text-chart-3";
  }
  return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700";
}

export default function ProjectOverviewPage() {
  const shellClassName = "h-full overflow-y-auto";
  const { projectId } = useParams();
  const [hasRequestedSuggestions, setHasRequestedSuggestions] = useState(false);
  const {
    window,
    windowPreset,
    startDate,
    endDate,
    setPreset,
    setCustomRange,
    isCustomInvalid,
  } = useTimeWindowFilter("ov");
  const {
    data: project,
    isLoading: isProjectLoading,
    isError: isProjectError,
    error: projectError,
  } = useProject(projectId);
  const {
    data: dashboard,
    isLoading: isDashboardLoading,
    isError: isDashboardError,
    error: dashboardError,
    refetch: refetchDashboard,
  } = useProjectDashboard(projectId, window);
  const {
    data: suggestionsResponse,
    isLoading: isSuggestionsLoading,
    isFetching: isSuggestionsFetching,
    isError: isSuggestionsError,
    refetch: refetchSuggestions,
  } = useAiSuggestions(projectId, 5, false);

  useEffect(() => {
    setHasRequestedSuggestions(false);
  }, [projectId]);

  if (!projectId) {
    return (
      <PageShell className={shellClassName}>
        <PageEmpty
          icon={AlertTriangle}
          title="Project not found"
          description="Please select a valid project."
        />
      </PageShell>
    );
  }

  if (isProjectLoading || (isDashboardLoading && !dashboard)) {
    return <PageLoading message="Loading project overview..." />;
  }

  if (isProjectError) {
    return (
      <PageShell className={shellClassName}>
        <QueryError message={getErrorMessage(projectError)} />
      </PageShell>
    );
  }

  if (isDashboardError) {
    return (
      <PageShell className={shellClassName}>
        <PageHeader title={project?.name ?? "Project Overview"} />
        <QueryError
          message={getErrorMessage(dashboardError)}
          onRetry={() => refetchDashboard()}
        />
      </PageShell>
    );
  }

  const data = dashboard;
  const summary = data?.summary ?? {
    total_tasks: 0,
    completed_tasks: 0,
    in_progress_tasks: 0,
    not_started_tasks: 0,
    overdue_tasks: 0,
    milestones: 0,
    milestones_completed: 0,
    percent_complete: 0,
  };
  const schedule = data?.schedule;
  const resources = data?.resources ?? {
    total_resources: 0,
    overallocated_count: 0,
  };
  const cost = data?.cost ?? {
    budget: null,
    total_cost: 0,
    actual_cost: 0,
    remaining_cost: 0,
  };
  const criticalPath = data?.critical_path ?? {
    task_count: 0,
    total_duration_days: 0,
    path_length_days: 0,
  };
  const upcomingMilestones = data?.upcoming_milestones ?? [];
  const overdueTasks = data?.overdue_tasks ?? [];
  const recentActivity = data?.recent_activity ?? [];
  const aiSuggestions = suggestionsResponse?.suggestions ?? [];
  const hasGeneratedSuggestions =
    hasRequestedSuggestions || Boolean(suggestionsResponse) || isSuggestionsError;

  const handleGenerateSuggestions = () => {
    setHasRequestedSuggestions(true);
    void refetchSuggestions();
  };

  return (
    <PageShell className={shellClassName}>
      <PageHeader
        title={project?.name ? `${project.name} Overview` : "Project Overview"}
        description="Project dashboard for execution, milestones, critical work, utilization, cost, and recent activity."
        action={
          <TimeWindowFilter
            value={windowPreset}
            startDate={startDate}
            endDate={endDate}
            onChange={setPreset}
            onCustomRangeChange={setCustomRange}
          />
        }
      />

      {isCustomInvalid ? (
        <QueryError message="For a custom window, please select both start and end date." />
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6 2xl:gap-4">
        <InsightsMetricCard
          compact
          label="Overall Completion"
          value={`${summary.percent_complete.toFixed(1)}%`}
          valueClassName="text-primary"
          to={`/projects/${projectId}/tasks`}
        />
        <InsightsMetricCard
          compact
          label="Total Tasks"
          value={summary.total_tasks}
          to={`/projects/${projectId}/tasks`}
        />
        <InsightsMetricCard
          compact
          label="Milestones"
          value={`${summary.milestones_completed}/${summary.milestones}`}
          to={`/projects/${projectId}/tasks`}
        />
        <InsightsMetricCard
          compact
          label="Critical Path"
          value={`${criticalPath.path_length_days}d`}
          hint={`${criticalPath.task_count} critical tasks`}
          valueClassName="text-destructive"
          to={`/projects/${projectId}/tasks`}
        />
        <InsightsMetricCard
          compact
          label="Resources"
          value={resources.total_resources}
          to={`/projects/${projectId}/resources`}
        />
        <InsightsMetricCard
          compact
          label="Overallocated"
          value={resources.overallocated_count}
          valueClassName="text-destructive"
          to={`/projects/${projectId}/utilization`}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1.05fr)_minmax(0,0.95fr)] xl:items-start">
        <div className="space-y-4">
          <Card className="py-4">
            <CardHeader className="px-4">
              <CardTitle className="text-sm font-semibold">Tasks by Status</CardTitle>
            </CardHeader>
            <CardContent className="px-4">
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Completed</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">
                    {summary.completed_tasks}
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">In Progress</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">
                    {summary.in_progress_tasks}
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Not Started</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">
                    {summary.not_started_tasks}
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Overdue</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums text-destructive">
                    {summary.overdue_tasks}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="py-4">
              <CardHeader className="px-4">
                <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                  <CalendarDays className="size-4 text-muted-foreground" />
                  Schedule Snapshot
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 px-4 sm:grid-cols-2">
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Start</p>
                  <p className="mt-1 text-sm font-medium">{schedule?.start_date ?? "-"}</p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Finish</p>
                  <p className="mt-1 text-sm font-medium">{schedule?.finish_date ?? "-"}</p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Duration</p>
                  <p className="mt-1 text-sm font-medium tabular-nums">
                    {schedule?.duration_days ?? 0}d
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Days Remaining</p>
                  <p className="mt-1 text-sm font-medium tabular-nums">
                    {schedule?.days_remaining ?? "-"}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="py-4">
              <CardHeader className="px-4">
                <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                  <Coins className="size-4 text-muted-foreground" />
                  Cost Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 px-4 sm:grid-cols-2">
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Budget</p>
                  <p className="mt-1 text-sm font-medium tabular-nums">
                    {cost.budget == null ? "-" : `$${cost.budget.toFixed(2)}`}
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Total Cost</p>
                  <p className="mt-1 text-sm font-medium tabular-nums">
                    ${cost.total_cost.toFixed(2)}
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Actual Cost</p>
                  <p className="mt-1 text-sm font-medium tabular-nums">
                    ${cost.actual_cost.toFixed(2)}
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Remaining Cost</p>
                  <p className="mt-1 text-sm font-medium tabular-nums">
                    ${cost.remaining_cost.toFixed(2)}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="py-4">
              <CardHeader className="px-4">
                <CardTitle className="text-sm font-semibold">Upcoming Milestones</CardTitle>
              </CardHeader>
              <CardContent className="px-4">
                {upcomingMilestones.length ? (
                  <ul className="space-y-2.5">
                    {upcomingMilestones.map((milestone) => (
                      <li key={milestone.task_id}>
                        <Link
                          to={`/projects/${projectId}/tasks`}
                          className="block rounded-lg border border-border/60 p-3 transition-colors hover:bg-muted/40"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <p className="truncate text-sm font-medium">{milestone.name}</p>
                            <span className="text-xs text-muted-foreground">
                              {milestone.finish_date}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">
                            Progress: {milestone.percent_complete.toFixed(1)}%
                          </p>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                    No upcoming milestones in the next 14 days.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="py-4">
              <CardHeader className="px-4">
                <CardTitle className="text-sm font-semibold">Overdue Tasks</CardTitle>
              </CardHeader>
              <CardContent className="px-4">
                {overdueTasks.length ? (
                  <ul className="space-y-2.5">
                    {overdueTasks.map((task) => (
                      <li key={task.task_id}>
                        <Link
                          to={`/projects/${projectId}/tasks`}
                          className="block rounded-lg border border-border/60 p-3 transition-colors hover:bg-muted/40"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <p className="truncate text-sm font-medium">{task.name}</p>
                            <span className="text-xs text-destructive">
                              {task.days_overdue}d overdue
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">
                            Finish: {task.finish_date} | Progress:{" "}
                            {task.percent_complete.toFixed(1)}%
                          </p>
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                    No overdue tasks detected.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="space-y-4">
          <Card className="py-4">
            <CardHeader className="px-4">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Route className="size-4 text-muted-foreground" />
                Critical Path Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 px-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Path Length</p>
                <p className="mt-1 text-lg font-semibold tabular-nums text-destructive">
                  {criticalPath.path_length_days}d
                </p>
              </div>
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Critical Tasks</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">
                  {criticalPath.task_count}
                </p>
              </div>
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Total Critical Work</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">
                  {criticalPath.total_duration_days}d
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="py-4">
            <CardHeader className="px-4">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Users className="size-4 text-muted-foreground" />
                Resource Utilization
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 px-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Active Resources</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">
                  {resources.total_resources}
                </p>
              </div>
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Overallocated</p>
                <p className="mt-1 text-lg font-semibold tabular-nums text-destructive">
                  {resources.overallocated_count}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="py-4">
            <CardHeader className="px-4">
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                  <Sparkles className="size-4 text-muted-foreground" />
                  AI Risk Signals
                </CardTitle>
                {hasGeneratedSuggestions ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="h-7 gap-1.5 text-xs"
                    onClick={handleGenerateSuggestions}
                    disabled={isSuggestionsFetching}
                  >
                    <RefreshCcw
                      className={isSuggestionsFetching ? "size-3.5 animate-spin" : "size-3.5"}
                    />
                    Refresh
                  </Button>
                ) : null}
              </div>
            </CardHeader>
            <CardContent className="px-4">
              {aiSuggestions.length ? (
                <ul className="space-y-2.5">
                  {aiSuggestions.map((suggestion) => (
                    <li key={suggestion.id} className="rounded-lg border border-border/60 p-3">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm font-medium">{suggestion.title}</p>
                        <Badge
                          variant="outline"
                          className={severityClassName(suggestion.severity)}
                        >
                          {suggestion.severity.toLowerCase()}
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {suggestion.description}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : !hasGeneratedSuggestions ? (
                <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                  <Sparkles className="mx-auto mb-3 size-5 text-muted-foreground" />
                  <p>Generate AI insights for this project on demand.</p>
                  <Button
                    type="button"
                    size="sm"
                    className="mt-4"
                    onClick={handleGenerateSuggestions}
                    disabled={isSuggestionsFetching}
                  >
                    Generate AI insights
                  </Button>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                  {isSuggestionsLoading || isSuggestionsFetching
                    ? "Generating AI insights..."
                    : isSuggestionsError
                      ? "AI insights are unavailable right now."
                      : "No AI risk signals surfaced for this project."}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <InsightsActivityCard
          title="Recent Project Activity"
          items={recentActivity}
          emptyMessage="No recent activity for this project."
          className="xl:sticky xl:top-6 xl:h-[calc(100dvh-11rem)]"
          contentClassName="flex h-full min-h-0 flex-col"
          listClassName="flex-1 overflow-y-auto pr-1"
        />
      </div>
    </PageShell>
  );
}
