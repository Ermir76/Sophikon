import { useParams } from "react-router";
import { AlertTriangle, CalendarDays } from "lucide-react";
import { useProject } from "@/features/projects/hooks/useProjects";
import { useProjectOverviewInsights } from "@/features/projects/hooks/useProjectOverviewInsights";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageEmpty } from "@/shared/components/state/PageEmpty";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { useTimeWindowFilter } from "@/shared/hooks/useTimeWindowFilter";
import { TimeWindowFilter } from "@/shared/ui/time-window-filter";
import { InsightsMetricCard } from "@/shared/ui/insights-metric-card";
import { InsightsTrendCard } from "@/shared/ui/insights-trend-card";
import { InsightsActivityCard } from "@/shared/ui/insights-activity-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";

export default function ProjectOverviewPage() {
  const { projectId } = useParams();
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
    data: insights,
    isLoading: isInsightsLoading,
    isError: isInsightsError,
    error: insightsError,
    refetch: refetchInsights,
  } = useProjectOverviewInsights(projectId, window);

  if (!projectId) {
    return (
      <PageShell>
        <PageEmpty
          icon={AlertTriangle}
          title="Project not found"
          description="Please select a valid project."
        />
      </PageShell>
    );
  }

  if (isProjectLoading || (isInsightsLoading && !insights)) {
    return <PageLoading message="Loading project overview..." />;
  }

  if (isProjectError) {
    return (
      <PageShell>
        <QueryError message={getErrorMessage(projectError)} />
      </PageShell>
    );
  }

  if (isInsightsError) {
    return (
      <PageShell>
        <PageHeader title={project?.name ?? "Project Overview"} />
        <QueryError
          message={getErrorMessage(insightsError)}
          onRetry={() => refetchInsights()}
        />
      </PageShell>
    );
  }

  const data = insights;
  const kpis = data?.kpis ?? {
    total_tasks: 0,
    completion_pct: 0,
    overdue_tasks: 0,
    critical_tasks: 0,
    total_resources: 0,
    overallocated_resources: 0,
  };
  const schedule = data?.schedule;

  return (
    <PageShell>
      <PageHeader
        title={project?.name ? `${project.name} Overview` : "Project Overview"}
        description="Project execution snapshot: progress, risk, schedule, and activity."
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

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <InsightsMetricCard
          label="Total Tasks"
          value={kpis.total_tasks}
          to={`/projects/${projectId}/tasks`}
        />
        <InsightsMetricCard
          label="Completion"
          value={`${kpis.completion_pct.toFixed(1)}%`}
          to={`/projects/${projectId}/tasks`}
        />
        <InsightsMetricCard
          label="Overdue Tasks"
          value={kpis.overdue_tasks}
          to={`/projects/${projectId}/tasks`}
        />
        <InsightsMetricCard
          label="Critical Tasks"
          value={kpis.critical_tasks}
          to={`/projects/${projectId}/tasks`}
        />
        <InsightsMetricCard
          label="Total Resources"
          value={kpis.total_resources}
          to={`/projects/${projectId}/resources`}
        />
        <InsightsMetricCard
          label="Overallocated"
          value={kpis.overallocated_resources}
          to={`/projects/${projectId}/utilization`}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.35fr_1fr]">
        <Card className="py-4">
          <CardHeader className="px-4">
            <CardTitle className="flex items-center gap-2 text-sm font-semibold">
              <CalendarDays className="size-4 text-muted-foreground" />
              Schedule Snapshot
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Start Date</p>
                <p className="mt-1 text-sm font-medium">{schedule?.start_date ?? "-"}</p>
              </div>
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Finish Date</p>
                <p className="mt-1 text-sm font-medium">{schedule?.finish_date ?? "-"}</p>
              </div>
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Days Remaining</p>
                <p className="mt-1 text-sm font-medium tabular-nums">
                  {schedule?.days_remaining ?? "-"}
                </p>
              </div>
              <div className="rounded-lg border border-border/60 p-3">
                <p className="text-xs text-muted-foreground">Milestones Due Soon</p>
                <p className="mt-1 text-sm font-medium tabular-nums">
                  {schedule?.milestones_due_soon ?? 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="py-4">
          <CardHeader className="px-4">
            <CardTitle className="flex items-center gap-2 text-sm font-semibold">
              <AlertTriangle className="size-4 text-muted-foreground" />
              At-Risk Tasks
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4">
            {data?.risk_items?.length ? (
              <ul className="space-y-3">
                {data.risk_items.map((item) => (
                  <li key={item.task_id} className="rounded-lg border border-border/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium">{item.name}</p>
                      {item.is_critical ? <Badge variant="destructive">Critical</Badge> : null}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{item.reason}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Finish: {item.finish_date} • Progress: {item.percent_complete.toFixed(1)}%
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                No elevated schedule risks detected in the selected window.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <InsightsTrendCard title="Project Execution Trend" data={data?.trend ?? []} />

      <InsightsActivityCard
        title="Recent Project Activity"
        items={data?.recent_activity ?? []}
        emptyMessage="No recent activity for this project."
      />
    </PageShell>
  );
}
