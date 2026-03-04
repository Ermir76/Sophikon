import { AlertTriangle } from "lucide-react";
import type { ResourceUtilization } from "@/features/resources/types";

export interface UtilizationSummaryCardsProps {
    resources: ResourceUtilization[];
    resourceColors: string[];
}

export function UtilizationSummaryCards({
    resources,
    resourceColors,
}: UtilizationSummaryCardsProps) {
    if (!resources || resources.length === 0) {
        return null;
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {resources.map((resource, i) => (
                <div
                    key={resource.resource_id}
                    className="rounded-lg border bg-card p-4 space-y-2"
                >
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div
                                className="size-3 rounded-full"
                                style={{ backgroundColor: resourceColors[i % resourceColors.length] }}
                            />
                            <span className="text-sm font-medium">{resource.resource_name}</span>
                        </div>
                        {Number(resource.peak_units) > Number(resource.max_units) && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-[10px] font-bold text-destructive">
                                <AlertTriangle className="size-3" />
                                Over
                            </span>
                        )}
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                        <div>
                            <span className="block text-foreground font-semibold text-lg">
                                {Math.round(Number(resource.peak_units) * 100)}%
                            </span>
                            Peak
                        </div>
                        <div>
                            <span className="block text-foreground font-semibold text-lg">
                                {Math.round(Number(resource.average_utilization) * 100)}%
                            </span>
                            Average
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
