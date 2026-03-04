import * as React from "react";
import { cn } from "@/shared/lib/utils";

interface PageHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
    title: string;
    description?: string;
    action?: React.ReactNode;
}

/**
 * Standardized header row for top-level pages.
 * Enforces `h1` semantic titles, muted descriptions, and right-aligned action slots.
 */
export function PageHeader({ title, description, action, className, ...props }: PageHeaderProps) {
    return (
        <div className={cn("flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4", className)} {...props}>
            <div className="space-y-1">
                <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
                {description && (
                    <p className="text-sm text-muted-foreground">{description}</p>
                )}
            </div>
            {action && (
                <div className="flex items-center gap-2">
                    {action}
                </div>
            )}
        </div>
    );
}
