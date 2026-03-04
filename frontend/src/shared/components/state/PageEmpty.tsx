import * as React from "react";
import { cn } from "@/shared/lib/utils";
import { FolderOpen } from "lucide-react";

interface PageEmptyProps extends React.HTMLAttributes<HTMLDivElement> {
    icon?: React.ElementType;
    title: string;
    description: string;
    action?: React.ReactNode;
}

/**
 * Standardized empty state component for pages with zero data.
 * Displays a muted icon, a bold title, description, and an optional primary CTA.
 */
export function PageEmpty({
    icon: Icon = FolderOpen,
    title,
    description,
    action,
    className,
    ...props
}: PageEmptyProps) {
    return (
        <div
            className={cn(
                "flex flex-col flex-1 items-center justify-center rounded-lg border border-dashed bg-card p-12 text-center animate-in fade-in-50",
                className
            )}
            {...props}
        >
            <div className="mx-auto flex size-14 items-center justify-center rounded-full bg-accent mb-4">
                <Icon className="size-7 text-muted-foreground" aria-hidden="true" />
            </div>
            <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
            <p className="mt-2 mb-6 text-sm text-muted-foreground max-w-sm">
                {description}
            </p>
            {action}
        </div>
    );
}
