import { format } from "date-fns";
import { AlertTriangle } from "lucide-react";

export interface OverAllocationItem {
    resource_name: string;
    date: string;
    allocated_units: number | string;
    max_units: number | string;
}

export interface OverAllocationsData {
    total_count: number;
    items: OverAllocationItem[];
}

export interface OverAllocationListProps {
    overAllocations?: OverAllocationsData | null;
    overAllocationCount: number;
}

export function OverAllocationList({
    overAllocations,
    overAllocationCount,
}: OverAllocationListProps) {
    if (overAllocationCount === 0 || !overAllocations) {
        return null;
    }

    return (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 space-y-3">
            <h4 className="text-sm font-semibold text-destructive flex items-center gap-2">
                <AlertTriangle className="size-4" />
                Over-Allocated Resources
            </h4>
            <div className="divide-y divide-destructive/10">
                {overAllocations.items.slice(0, 10).map((item, i) => (
                    <div key={i} className="flex items-center justify-between py-2 text-sm">
                        <div className="flex items-center gap-3">
                            <span className="font-medium">{item.resource_name}</span>
                            <span className="text-muted-foreground">
                                {format(new Date(item.date), "MMM d, yyyy")}
                            </span>
                        </div>
                        <div className="flex items-center gap-2 text-destructive font-medium">
                            <span>{Math.round(Number(item.allocated_units) * 100)}%</span>
                            <span className="text-muted-foreground/60">/</span>
                            <span className="text-muted-foreground">
                                {Math.round(Number(item.max_units) * 100)}%
                            </span>
                        </div>
                    </div>
                ))}
                {overAllocations.items.length > 10 && (
                    <p className="text-xs text-muted-foreground pt-2">
                        … and {overAllocations.items.length - 10} more
                    </p>
                )}
            </div>
        </div>
    );
}
