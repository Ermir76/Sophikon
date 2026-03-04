import { AlertTriangle } from "lucide-react";

interface OverAllocationBadgeProps {
    className?: string;
}

export function OverAllocationBadge({ className }: OverAllocationBadgeProps) {
    return (
        <span
            className={`inline-flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-[10px] font-bold tracking-wide text-destructive border border-destructive/20 ${className ?? ""}`}
        >
            <AlertTriangle className="size-3" />
            Over-allocated
        </span>
    );
}
