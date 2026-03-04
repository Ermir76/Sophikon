import * as React from "react";
import { cn } from "@/shared/lib/utils";

interface PageShellProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
}

/**
 * A consistent wrapper for all top-level application pages.
 * Enforces standard 24px (p-6) padding and standard vertical rhythm layout gaps.
 */
export function PageShell({ children, className, ...props }: PageShellProps) {
    return (
        <div
            className={cn("flex flex-col space-y-6 p-6 overflow-x-hidden min-h-0", className)}
            {...props}
        >
            {children}
        </div>
    );
}
