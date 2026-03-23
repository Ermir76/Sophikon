import { Search } from "lucide-react";
import { Input } from "@/shared/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/shared/ui/select";
import {
    KANBAN_COLUMNS,
    KANBAN_LANE_MODE_OPTIONS,
    type KanbanLaneMode,
    type PriorityFilter,
    type TaskStatus,
} from "../types";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/ui/tooltip";

export type { PriorityFilter };

interface KanbanToolbarProps {
    searchQuery: string;
    onSearchChange: (value: string) => void;
    priorityFilter: PriorityFilter;
    onPriorityFilterChange: (value: PriorityFilter) => void;
    laneMode: KanbanLaneMode;
    onLaneModeChange: (value: KanbanLaneMode) => void;
    selectionMode: boolean;
    selectedCount: number;
    bulkMoveTarget: TaskStatus;
    isBulkMovePending: boolean;
    onSelectionModeChange: (enabled: boolean) => void;
    onBulkMoveTargetChange: (value: TaskStatus) => void;
    onBulkMove: () => void;
    onClearSelection: () => void;
}

export function KanbanToolbar({
    searchQuery,
    onSearchChange,
    priorityFilter,
    onPriorityFilterChange,
    laneMode,
    onLaneModeChange,
    selectionMode,
    selectedCount,
    bulkMoveTarget,
    isBulkMovePending,
    onSelectionModeChange,
    onBulkMoveTargetChange,
    onBulkMove,
    onClearSelection,
}: KanbanToolbarProps) {
    return (
        <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-xs">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
                <Input
                    placeholder="Search tasks..."
                    value={searchQuery}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="pl-8 h-9"
                />
            </div>
            <Select
                value={priorityFilter}
                onValueChange={(v) => onPriorityFilterChange(v as PriorityFilter)}
            >
                <SelectTrigger className="w-[160px] h-9">
                    <SelectValue placeholder="All priorities" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">All priorities</SelectItem>
                    <SelectItem value="high">High (&gt;= 750)</SelectItem>
                    <SelectItem value="medium">Medium (&gt;= 500)</SelectItem>
                    <SelectItem value="low">Low (&gt;= 250)</SelectItem>
                    <SelectItem value="minimal">Minimal</SelectItem>
                </SelectContent>
            </Select>
            <Select
                value={laneMode}
                onValueChange={(value) => onLaneModeChange(value as KanbanLaneMode)}
            >
                <SelectTrigger className="w-[220px] h-9">
                    <SelectValue placeholder="No swimlanes" />
                </SelectTrigger>
                <SelectContent>
                    {KANBAN_LANE_MODE_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                            {option.label}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
            <button
                type="button"
                className={`h-9 rounded-md border px-3 text-xs font-medium transition-colors ${
                    selectionMode
                        ? "border-primary/40 bg-primary/10 text-primary hover:bg-primary/15"
                        : "border-border text-muted-foreground hover:bg-muted/50"
                }`}
                onClick={() => onSelectionModeChange(!selectionMode)}
                aria-label="Toggle bulk selection mode"
            >
                {selectionMode ? "Exit select" : "Select"}
            </button>
            {selectionMode && (
                <>
                    <span className="text-xs font-medium text-muted-foreground">
                        {selectedCount} selected
                    </span>
                    <Select
                        value={bulkMoveTarget}
                        onValueChange={(value) => onBulkMoveTargetChange(value as TaskStatus)}
                    >
                        <SelectTrigger className="w-[180px] h-9">
                            <SelectValue placeholder="Move to column" />
                        </SelectTrigger>
                        <SelectContent>
                            {KANBAN_COLUMNS.map((column) => (
                                <SelectItem key={column.id} value={column.id}>
                                    {column.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <button
                        type="button"
                        className="h-9 rounded-md border border-border px-3 text-xs font-medium text-muted-foreground hover:bg-muted/50 disabled:cursor-not-allowed disabled:opacity-50"
                        onClick={onClearSelection}
                        disabled={selectedCount === 0 || isBulkMovePending}
                    >
                        Clear
                    </button>
                    <button
                        type="button"
                        className="h-9 rounded-md border border-primary/40 bg-primary/10 px-3 text-xs font-medium text-primary hover:bg-primary/15 disabled:cursor-not-allowed disabled:opacity-50"
                        onClick={onBulkMove}
                        disabled={selectedCount === 0 || isBulkMovePending}
                    >
                        {isBulkMovePending ? "Moving..." : "Move selected"}
                    </button>
                </>
            )}
            <Tooltip>
                <TooltipTrigger asChild>
                    <button
                        type="button"
                        className="h-9 rounded-md border border-border px-3 text-xs font-medium text-muted-foreground hover:bg-muted/50"
                        aria-label="Keyboard shortcuts help"
                    >
                        Shortcuts
                    </button>
                </TooltipTrigger>
                <TooltipContent className="space-y-1 text-xs">
                    <p><kbd className="rounded border border-border bg-muted px-1 py-0.5">N</kbd> Quick-add in focused column</p>
                    <p><kbd className="rounded border border-border bg-muted px-1 py-0.5">Arrow keys</kbd> Move card focus</p>
                    <p><kbd className="rounded border border-border bg-muted px-1 py-0.5">Enter</kbd> Open focused card</p>
                </TooltipContent>
            </Tooltip>
        </div>
    );
}
