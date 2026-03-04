import { useState, useMemo } from "react";
import { useParams, Navigate } from "react-router";
import { AlertTriangle } from "lucide-react";
import { format, addDays, subDays } from "date-fns";

import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { QueryError } from "@/shared/components/QueryError";
import { useProjectUtilization, useOverAllocations } from "@/features/resources/hooks/useUtilization";
import type { DailyAllocation, ResourceUtilization } from "@/features/resources/types";

import { UtilizationChart } from "../components/UtilizationChart";
import { OverAllocationList } from "../components/OverAllocationList";
import { UtilizationSummaryCards } from "../components/UtilizationSummaryCards";

// ── Color palette for resource bars ──
const RESOURCE_COLORS = [
    "hsl(221, 83%, 53%)",  // blue
    "hsl(262, 83%, 58%)",  // violet
    "hsl(142, 71%, 45%)",  // green
    "hsl(38, 92%, 50%)",   // amber
    "hsl(340, 82%, 52%)",  // rose
    "hsl(199, 89%, 48%)",  // sky
    "hsl(25, 95%, 53%)",   // orange
    "hsl(173, 80%, 40%)",  // teal
];

const OVER_ALLOCATED_COLOR = "hsl(0, 84%, 60%)";

export default function UtilizationPage() {
    const { projectId } = useParams<{ projectId: string }>();

    // Default date range: today ± 14 days
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
    } = useOverAllocations(projectId, startDate, endDate);

    // Transform data for Recharts: one entry per day, one key per resource
    const chartData = useMemo(() => {
        if (!utilization?.resources?.length) return [];

        // Use the first resource's daily_allocations to get the date range
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
        [utilization],
    );

    const overAllocationCount = overAllocations?.total_count ?? 0;

    if (!projectId) {
        return <Navigate to="/projects" replace />;
    }

    if (isError) {
        return (
            <div className="p-6">
                <QueryError message="Failed to load utilization data." onRetry={() => refetch()} />
            </div>
        );
    }

    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-2xl font-medium">Resource Utilization</h3>
                    <p className="text-sm text-muted-foreground">
                        Time-phased resource allocation across the project.
                    </p>
                </div>
                {overAllocationCount > 0 && (
                    <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
                        <AlertTriangle className="size-4" />
                        {overAllocationCount} over-allocation{overAllocationCount !== 1 ? "s" : ""}
                    </div>
                )}
            </div>

            {/* Date Range Controls */}
            <div className="flex items-end gap-4">
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
                isLoading={isLoading}
                resourceColors={RESOURCE_COLORS}
                overAllocatedColor={OVER_ALLOCATED_COLOR}
            />

            <OverAllocationList
                overAllocations={overAllocations}
                overAllocationCount={overAllocationCount}
            />

            <UtilizationSummaryCards
                resources={utilization?.resources ?? []}
                resourceColors={RESOURCE_COLORS}
            />
        </div>
    );
}
