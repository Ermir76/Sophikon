import { format, addDays, subDays } from "date-fns";
import { AlertTriangle } from "lucide-react";
import { useMemo, useState } from "react";
import { Navigate, useParams } from "react-router";

import { useOverAllocations, useProjectUtilization } from "@/features/resources/hooks/useUtilization";
import type { DailyAllocation, ResourceUtilization } from "@/features/resources/types";
import { QueryError } from "@/shared/components/QueryError";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageEmpty } from "@/shared/components/state/PageEmpty";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

import { OverAllocationList } from "@/features/resources/components/OverAllocationList";
import { UtilizationChart } from "@/features/resources/components/UtilizationChart";
import { UtilizationSummaryCards } from "@/features/resources/components/UtilizationSummaryCards";

const RESOURCE_COLORS = [
  "var(--resource-series-1)",
  "var(--resource-series-2)",
  "var(--resource-series-3)",
  "var(--resource-series-4)",
  "var(--resource-series-5)",
  "var(--resource-series-6)",
  "var(--resource-series-7)",
  "var(--resource-series-8)",
];

const OVER_ALLOCATED_COLOR = "var(--status-overallocated)";

export default function UtilizationPage() {
  const shellClassName = "h-full overflow-y-auto";
  const { projectId } = useParams<{ projectId: string }>();

  const today = new Date();
  const [startDate, setStartDate] = useState(format(subDays(today, 7), "yyyy-MM-dd"));
  const [endDate, setEndDate] = useState(format(addDays(today, 21), "yyyy-MM-dd"));

  const {
    data: utilization,
    isLoading,
    isError,
    refetch,
  } = useProjectUtilization(projectId, startDate, endDate);

  const {
    data: overAllocations,
    isError: isOverAllocationsError,
    refetch: refetchOverAllocations,
  } = useOverAllocations(projectId, startDate, endDate);

  const chartData = useMemo(() => {
    if (!utilization?.resources?.length) return [];

    const dateCount = utilization.resources[0]?.daily_allocations?.length ?? 0;
    if (dateCount === 0) return [];

    const entries: Record<string, unknown>[] = [];

    for (let i = 0; i < dateCount; i++) {
      const entry: Record<string, unknown> = {
        date: utilization.resources[0].daily_allocations[i].date,
        dateLabel: format(new Date(utilization.resources[0].daily_allocations[i].date), "MMM d"),
      };

      let totalAllocated = 0;
      let maxUnits = 1;

      for (const resource of utilization.resources) {
        const day: DailyAllocation | undefined = resource.daily_allocations[i];
        const units = day ? Number(day.allocated_units) : 0;
        entry[resource.resource_name] = units;
        totalAllocated += units;
        maxUnits = Math.max(maxUnits, Number(day?.max_units ?? 1));
      }

      entry._totalAllocated = totalAllocated;
      entry._isOverAllocated = totalAllocated > maxUnits;
      entry._maxUnits = maxUnits;
      entries.push(entry);
    }

    return entries;
  }, [utilization]);

  const resourceNames = useMemo(
    () => utilization?.resources?.map((r: ResourceUtilization) => r.resource_name) ?? [],
    [utilization]
  );

  const overAllocationCount = overAllocations?.total_count ?? 0;

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  if (isError) {
    return (
      <PageShell className={shellClassName}>
        <QueryError message="Failed to load utilization data." onRetry={() => refetch()} />
      </PageShell>
    );
  }

  if (isLoading) {
    return (
      <PageShell className={shellClassName}>
        <PageHeader
          title="Resource Utilization"
          description="Monitor workload trends and over-allocation risk."
        />
        <PageLoading message="Loading utilization data..." />
      </PageShell>
    );
  }

  if (chartData.length === 0) {
    return (
      <PageShell className={shellClassName}>
        <PageHeader
          title="Resource Utilization"
          description="Monitor workload trends and over-allocation risk."
        />
        <PageEmpty
          title="No utilization data"
          description="Assign resources to tasks to see utilization over time."
        />
      </PageShell>
    );
  }

  return (
    <PageShell className={shellClassName}>
      <PageHeader
        title="Resource Utilization"
        description="Monitor workload trends and over-allocation risk."
        action={
          overAllocationCount > 0 ? (
            <Badge
              variant="outline"
              className="gap-2 border-destructive/40 px-3 py-1.5 text-sm font-medium text-destructive"
            >
              <AlertTriangle className="size-4" />
              {overAllocationCount} over-allocation{overAllocationCount !== 1 ? "s" : ""}
            </Badge>
          ) : null
        }
      />

      <div className="flex flex-wrap items-end gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="util-start">Start Date</Label>
          <Input
            id="util-start"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-40"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="util-end">End Date</Label>
          <Input
            id="util-end"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-40"
          />
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          Refresh
        </Button>
      </div>

      <UtilizationChart
        chartData={chartData}
        resourceNames={resourceNames}
        resourceColors={RESOURCE_COLORS}
        overAllocatedColor={OVER_ALLOCATED_COLOR}
      />

      {isOverAllocationsError ? (
        <QueryError
          message="Failed to load over-allocation data."
          onRetry={() => refetchOverAllocations()}
        />
      ) : (
        <OverAllocationList
          overAllocations={overAllocations}
          overAllocationCount={overAllocationCount}
        />
      )}

      <UtilizationSummaryCards
        resources={utilization?.resources ?? []}
        resourceColors={RESOURCE_COLORS}
      />
    </PageShell>
  );
}
