import { ChevronsLeft, Plus } from "lucide-react";
import { Button } from "@/shared/ui/button";
import type { KanbanColumn } from "../types";

interface KanbanColumnHeaderProps {
    column: KanbanColumn;
    count: number;
    onToggleCollapse: () => void;
    onAdd?: () => void;
}

export function KanbanColumnHeader({ column, count, onToggleCollapse, onAdd }: KanbanColumnHeaderProps) {
    return (
        <div className="flex items-center justify-between px-3 py-2.5 shrink-0 border-b border-border">
            <div className="flex items-center gap-2">
                <span className={`text-base leading-none ${column.color}`}>●</span>
                <span className="text-sm font-semibold">{column.label}</span>
                <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full min-w-[1.25rem] text-center">
                    {count}
                </span>
            </div>
            <div className="flex items-center gap-1">
                <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-6 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity"
                    onClick={onAdd}
                    aria-label={`Add task to ${column.label}`}
                >
                    <Plus className="size-3.5" />
                </Button>
                <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-6 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity"
                    onClick={onToggleCollapse}
                    aria-label={`Collapse ${column.label}`}
                    aria-expanded={true}
                >
                    <ChevronsLeft className="size-3.5" />
                </Button>
            </div>
        </div>
    );
}
