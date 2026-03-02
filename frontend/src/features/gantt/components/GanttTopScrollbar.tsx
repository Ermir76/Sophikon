import { forwardRef } from "react";

interface GanttTopScrollbarProps {
    totalWidth: number;
    onScroll: () => void;
}

export const GanttTopScrollbar = forwardRef<HTMLDivElement, GanttTopScrollbarProps>(
    ({ totalWidth, onScroll }, ref) => {
        return (
            <div
                ref={ref}
                className="overflow-x-auto overflow-y-hidden"
                style={{ height: 12 }}
                onScroll={onScroll}
            >
                <div style={{ width: totalWidth, height: 1 }} />
            </div>
        );
    }
);

GanttTopScrollbar.displayName = "GanttTopScrollbar";
