import { useState } from "react";
import { Link } from "react-router";
import { useOrgStore, useOrganization, useOrganizations } from "@/features/organizations";
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
import { Button } from "@/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

export default function DashboardPage() {
  const shellClassName = "h-full overflow-y-auto";
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
    isLoading: isOrgsLoading,
    isError: isOrgsError,
    error: orgsError,
    refetch: refetchOrganizations,
  } = useOrganizations();
  const {
    data: insights,
    isLoading: isInsightsLoading,
    isFetching: isInsightsFetching,
    isError: isInsightsError,
    error: insightsError,
    refetch: refetchInsights,
  } = useDashboardInsights(activeOrgId, window);

  if (
    isOrgLoading ||
    (!activeOrgId && isOrgsLoading) ||
    (isInsightsLoading && !!activeOrgId && !insights)
  ) {
    return <PageLoading message="Loading dashboard..." />;
  }

  if (isOrgError) {
    return (
      <PageShell className={shellClassName}>
        <QueryError message={getErrorMessage(orgError)} />
      </PageShell>
    );
  }

  if (!activeOrgId && isOrgsError) {
    return (
      <PageShell className={shellClassName}>
        <QueryError
          message={getErrorMessage(orgsError)}
          onRetry={() => refetchOrganizations()}
        />
      </PageShell>
    );
  }

  if (!activeOrganization) {
    return (
      <PageShell className={shellClassName}>
        <PageEmpty
          title="Welcome to Sophikon"
          description="Please select or create an organization to get started."
        />
      </PageShell>
    );
  }

  if (isInsightsError) {
    return (
      <PageShell className={shellClassName}>
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
    <PageShell className={shellClassName}>
      <PageHeader
        title={`${activeOrganization.name} Dashboard`}
        description="Fast control-center view of execution, risk, and activity."
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
        <InsightsMetricCard compact label="Active Projects" value={kpis.active_projects} to="/projects" />
        <InsightsMetricCard
          compact
          label="Completed Projects"
          value={kpis.completed_projects}
          valueClassName="text-emerald-600 dark:text-emerald-400"
          to="/projects"
        />
        <InsightsMetricCard
          compact
          label="Task Completion"
          value={`${kpis.task_completion_pct.toFixed(1)}%`}
          valueClassName="text-primary"
          to="/projects"
        />
        <InsightsMetricCard
          compact
          label="Overdue Tasks"
          value={kpis.overdue_tasks}
          valueClassName="text-destructive"
          to="/projects"
        />
        <InsightsMetricCard
          compact
          label="Critical Tasks"
          value={kpis.critical_tasks}
          valueClassName="text-destructive"
          to="/projects"
        />
        <InsightsMetricCard
          compact
          label="Overallocated Resources"
          value={kpis.overallocated_resources}
          valueClassName="text-destructive"
          to="/projects"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1.05fr)_minmax(0,0.95fr)] xl:items-start">
        <div className={cn(isInsightsFetching && "opacity-90")}>
          <InsightsTrendCard
            title="Execution Trend"
            data={data?.trend ?? []}
            chartClassName="h-[280px] 2xl:h-[310px]"
          />
        </div>

        <Card className="py-4">
          <CardHeader className="px-4">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-sm font-semibold">Project Health</CardTitle>
              <div className="flex items-center gap-2">
                {refreshingHint}
                <Button
                  type="button"
                  size="sm"
                  variant={healthSort === "risk" ? "secondary" : "outline"}
                  className="h-7 text-xs"
                  onClick={() => setHealthSort("risk")}
                >
                  Risk
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={healthSort === "completion" ? "secondary" : "outline"}
                  className="h-7 text-xs"
                  onClick={() => setHealthSort("completion")}
                >
                  Completion
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="px-4">
            {projectHealth.length === 0 ? (
              <p className="text-sm text-muted-foreground">No project health data yet.</p>
            ) : (
              <div className="max-h-[320px] overflow-auto pr-1">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-xs">Project</TableHead>
                      <TableHead className="text-xs">Status</TableHead>
                      <TableHead className="text-right text-xs">Done</TableHead>
                      <TableHead className="text-right text-xs">Overdue</TableHead>
                      <TableHead className="text-right text-xs">Critical</TableHead>
                      <TableHead className="text-right text-xs">Risk</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {projectHealth.map((row) => (
                      <TableRow key={row.project_id} className="h-10">
                        <TableCell className="font-medium">
                          <Link to={`/projects/${row.project_id}`} className="hover:underline">
                            {row.name}
                          </Link>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">{row.status}</TableCell>
                        <TableCell className="text-right tabular-nums">{row.completion_pct.toFixed(1)}%</TableCell>
                        <TableCell className="text-right tabular-nums">{row.overdue_tasks}</TableCell>
                        <TableCell className="text-right tabular-nums">{row.critical_tasks}</TableCell>
                        <TableCell className="text-right">
                          <div className="inline-flex items-center gap-2">
                            <span className="tabular-nums">{row.risk_score.toFixed(1)}</span>
                            <Badge
                              variant="outline"
                              className={cn(
                                "capitalize",
                                row.risk_level === "high" && "border-destructive/50 bg-destructive/15 text-destructive",
                                row.risk_level === "medium" && "border-chart-3/50 bg-chart-3/15 text-chart-3",
                              )}
                            >
                              {row.risk_level}
                            </Badge>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        <InsightsActivityCard
          title="Recent Activity"
          items={data?.recent_activity ?? []}
          emptyMessage="No recent activity to show."
          className="xl:sticky xl:top-6 xl:h-[calc(100dvh-11rem)]"
          contentClassName="flex h-full min-h-0 flex-col"
          listClassName="flex-1 overflow-y-auto pr-1"
        />
      </div>
    </PageShell>
  );
}
