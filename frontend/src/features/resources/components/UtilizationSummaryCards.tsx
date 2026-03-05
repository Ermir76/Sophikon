import { AlertTriangle } from "lucide-react";
import type { ResourceUtilization } from "@/features/resources/types";
import { Card, CardContent } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";

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
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {resources.map((resource, i) => (
                <Card key={resource.resource_id}>
                    <CardContent className="space-y-2 p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div
                                className="size-3 rounded-full"
                                style={{ backgroundColor: resourceColors[i % resourceColors.length] }}
                            />
                            <span className="text-sm font-medium">{resource.resource_name}</span>
                        </div>
                        {Number(resource.peak_units) > Number(resource.max_units) && (
                            <Badge variant="outline" className="gap-1 border-destructive/40 text-destructive">
                                <AlertTriangle className="size-3" />
                                Over
                            </Badge>
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
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}
