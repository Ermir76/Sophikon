import { useState } from "react";
import { Link } from "react-router";
import { useOrgStore, useOrganization } from "@/features/organizations";
import { useDashboardInsights } from "@/features/dashboard/hooks/useDashboardInsights";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageEmpty } from "@/shared/components/state/PageEmpty";
import { useTimeWindowFilter } from "@/shared/hooks/useTimeWindowFilter";
import { TimeWindowFilter } from "@/shared/ui/time-window-filter";
import { InsightsMetricCard } from "@/shared/ui/insights-metric-card";
import { InsightsTrendCard } from "@/shared/ui/insights-trend-card";
import { InsightsActivityCard } from "@/shared/ui/insights-activity-card";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

export default function DashboardPage() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const [healthSort, setHealthSort] = useState<"risk" | "completion">("risk");
  const {
    window,
    windowPreset,
    startDate,
    endDate,
    setPreset,
    setCustomRange,
    isCustomInvalid,
  } = useTimeWindowFilter("dash");

  const {
    data: activeOrganization,
    isLoading: isOrgLoading,
    isError: isOrgError,
    error: orgError,
  } = useOrganization(activeOrgId);
  const {
    data: insights,
    isLoading: isInsightsLoading,
    isFetching: isInsightsFetching,
    isError: isInsightsError,
    error: insightsError,
    refetch: refetchInsights,
  } = useDashboardInsights(activeOrgId, window);

  if (isOrgLoading || (isInsightsLoading && !!activeOrgId && !insights)) {
    return <PageLoading message="Loading dashboard..." />;
  }

  if (isOrgError) {
    return (
      <PageShell>
        <QueryError message={getErrorMessage(orgError)} />
      </PageShell>
    );
  }

  if (!activeOrganization) {
    return (
      <PageShell>
        <PageEmpty
          title="Welcome to Sophikon"
          description="Please select or create an organization to get started."
        />
      </PageShell>
    );
  }

  if (isInsightsError) {
    return (
      <PageShell>
        <PageHeader
          title={`${activeOrganization.name} Dashboard`}
          description="Overview of your projects and organization metrics."
        />
        <QueryError
          message={getErrorMessage(insightsError)}
          onRetry={() => refetchInsights()}
        />
      </PageShell>
    );
  }

  const data = insights;
  const firstProjectId = data?.project_health?.[0]?.project_id;
  const projectHealth = [...(data?.project_health ?? [])];
  if (healthSort === "completion") {
    projectHealth.sort((a, b) => b.completion_pct - a.completion_pct);
  } else {
    projectHealth.sort((a, b) => b.risk_score - a.risk_score);
  }

  const kpis = data?.kpis ?? {
    active_projects: 0,
    completed_projects: 0,
    task_completion_pct: 0,
    overdue_tasks: 0,
    critical_tasks: 0,
    overallocated_resources: 0,
  };

  const refreshingHint = isInsightsFetching ? (
    <span className="text-xs text-muted-foreground">Refreshing...</span>
  ) : null;

  return (
    <PageShell>
      <PageHeader
        title={`${activeOrganization.name} Dashboard`}
        description="Overview of your projects and organization metrics."
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
        <InsightsMetricCard label="Active Projects" value={kpis.active_projects} to="/projects" />
        <InsightsMetricCard label="Completed Projects" value={kpis.completed_projects} to="/projects" />
        <InsightsMetricCard
          label="Task Completion"
          value={`${kpis.task_completion_pct.toFixed(1)}%`}
          to={firstProjectId ? `/projects/${firstProjectId}/tasks` : "/projects"}
        />
        <InsightsMetricCard
          label="Overdue Tasks"
          value={kpis.overdue_tasks}
          to={firstProjectId ? `/projects/${firstProjectId}/tasks` : "/projects"}
        />
        <InsightsMetricCard
          label="Critical Tasks"
          value={kpis.critical_tasks}
          to={firstProjectId ? `/projects/${firstProjectId}/tasks` : "/projects"}
        />
        <InsightsMetricCard
          label="Overallocated Resources"
          value={kpis.overallocated_resources}
          to={firstProjectId ? `/projects/${firstProjectId}/utilization` : "/projects"}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.45fr_1fr]">
        <Card className="py-4">
          <CardHeader className="px-4">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-sm font-semibold">Project Health</CardTitle>
              <div className="flex items-center gap-2 text-xs">
                {refreshingHint}
                <button
                  type="button"
                  className="rounded-md border px-2 py-1 text-muted-foreground hover:bg-accent"
                  onClick={() => setHealthSort("risk")}
                >
                  Sort: Risk
                </button>
                <button
                  type="button"
                  className="rounded-md border px-2 py-1 text-muted-foreground hover:bg-accent"
                  onClick={() => setHealthSort("completion")}
                >
                  Sort: Completion
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="px-4">
            {projectHealth.length === 0 ? (
              <p className="text-sm text-muted-foreground">No project health data yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Project</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Completion</TableHead>
                    <TableHead className="text-right">Overdue</TableHead>
                    <TableHead className="text-right">Critical</TableHead>
                    <TableHead className="text-right">Risk</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {projectHealth.map((row) => (
                    <TableRow key={row.project_id}>
                      <TableCell className="font-medium">
                        <Link to={`/projects/${row.project_id}`} className="hover:underline">
                          {row.name}
                        </Link>
                      </TableCell>
                      <TableCell>{row.status}</TableCell>
                      <TableCell className="text-right tabular-nums">{row.completion_pct.toFixed(1)}%</TableCell>
                      <TableCell className="text-right tabular-nums">{row.overdue_tasks}</TableCell>
                      <TableCell className="text-right tabular-nums">{row.critical_tasks}</TableCell>
                      <TableCell className="text-right">
                        <div className="inline-flex items-center gap-2">
                          <span className="tabular-nums">{row.risk_score.toFixed(1)}</span>
                          <Badge
                            variant={
                              row.risk_level === "high"
                                ? "destructive"
                                : row.risk_level === "medium"
                                  ? "secondary"
                                  : "outline"
                            }
                          >
                            {row.risk_level}
                          </Badge>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <InsightsActivityCard
          title="Recent Activity"
          items={data?.recent_activity ?? []}
          emptyMessage="No recent activity to show."
        />
      </div>

      <div className={cn(isInsightsFetching && "opacity-90")}>
        <InsightsTrendCard
          title="Execution Trend"
          data={data?.trend ?? []}
        />
      </div>
    </PageShell>
  );
}
