import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ChevronsLeft, Plus, SlidersHorizontal } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import {
    Popover,
    PopoverContent,
    PopoverHeader,
    PopoverTitle,
    PopoverDescription,
    PopoverTrigger,
} from "@/shared/ui/popover";
import type { KanbanColumn } from "../types";

interface KanbanColumnHeaderProps {
    column: KanbanColumn;
    count: number;
    limit?: number;
    isOverLimit?: boolean;
    onToggleCollapse?: () => void;
    onAdd?: () => void;
    onSetWipLimit?: (limit: number | null) => void;
}

export function KanbanColumnHeader({
    column,
    count,
    limit,
    isOverLimit = false,
    onToggleCollapse,
    onAdd,
    onSetWipLimit,
}: KanbanColumnHeaderProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [limitInput, setLimitInput] = useState(limit ? String(limit) : "");

    useEffect(() => {
        setLimitInput(limit ? String(limit) : "");
    }, [limit]);

    const parsedLimit = useMemo(() => {
        const normalized = limitInput.trim();
        if (!normalized) return null;
        const value = Number(normalized);
        if (!Number.isInteger(value) || value < 1 || value > 999) return null;
        return value;
    }, [limitInput]);

    const countLabel = limit ? `${count}/${limit}` : String(count);

    return (
        <div className="flex items-center justify-between px-3 py-2.5 shrink-0 border-b border-border">
            <div className="flex items-center gap-2">
                <span className={`text-base leading-none ${column.color}`}>●</span>
                <span className="text-sm font-semibold">{column.label}</span>
                <span
                    className={`text-xs px-1.5 py-0.5 rounded-full min-w-[1.25rem] text-center ${
                        isOverLimit
                            ? "bg-destructive/15 text-destructive font-semibold"
                            : "text-muted-foreground bg-muted"
                    }`}
                    aria-label={
                        limit
                            ? `${column.label} has ${count} tasks out of limit ${limit}`
                            : `${column.label} has ${count} tasks`
                    }
                >
                    {countLabel}
                </span>
                {isOverLimit && (
                    <AlertTriangle
                        className="size-3.5 text-destructive"
                        aria-label={`${column.label} WIP limit exceeded`}
                    />
                )}
            </div>
            <div className="flex items-center gap-1">
                <Popover open={isOpen} onOpenChange={setIsOpen}>
                    <PopoverTrigger asChild>
                        <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="size-6 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity"
                            aria-label={`Set WIP limit for ${column.label}`}
                        >
                            <SlidersHorizontal className="size-3.5" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-64" align="end">
                        <PopoverHeader>
                            <PopoverTitle>WIP limit</PopoverTitle>
                            <PopoverDescription>
                                Set max cards for {column.label}.
                            </PopoverDescription>
                        </PopoverHeader>
                        <div className="mt-3 space-y-3">
                            <Input
                                type="number"
                                min={1}
                                max={999}
                                value={limitInput}
                                onChange={(event) => setLimitInput(event.target.value)}
                                placeholder="No limit"
                                aria-label={`WIP limit value for ${column.label}`}
                            />
                            <div className="flex items-center justify-end gap-2">
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                        onSetWipLimit?.(null);
                                        setIsOpen(false);
                                    }}
                                >
                                    Clear
                                </Button>
                                <Button
                                    type="button"
                                    size="sm"
                                    disabled={parsedLimit === null}
                                    onClick={() => {
                                        if (parsedLimit === null) return;
                                        onSetWipLimit?.(parsedLimit);
                                        setIsOpen(false);
                                    }}
                                >
                                    Save
                                </Button>
                            </div>
                        </div>
                    </PopoverContent>
                </Popover>
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
