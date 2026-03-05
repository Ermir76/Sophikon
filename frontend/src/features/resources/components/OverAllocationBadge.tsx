import { AlertTriangle } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { cn } from "@/shared/lib/utils";

interface OverAllocationBadgeProps {
    className?: string;
}

export function OverAllocationBadge({ className }: OverAllocationBadgeProps) {
    return (
        <Badge
            variant="outline"
            className={cn("gap-1 border-destructive/40 text-destructive", className)}
        >
            <AlertTriangle className="size-3" />
            Over-allocated
        </Badge>
    );
}
