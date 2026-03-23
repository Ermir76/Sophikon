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
    KANBAN_LANE_MODE_OPTIONS,
    type KanbanLaneMode,
    type PriorityFilter,
} from "../types";

export type { PriorityFilter };

interface KanbanToolbarProps {
    searchQuery: string;
    onSearchChange: (value: string) => void;
    priorityFilter: PriorityFilter;
    onPriorityFilterChange: (value: PriorityFilter) => void;
    laneMode: KanbanLaneMode;
    onLaneModeChange: (value: KanbanLaneMode) => void;
}

export function KanbanToolbar({
    searchQuery,
    onSearchChange,
    priorityFilter,
    onPriorityFilterChange,
    laneMode,
    onLaneModeChange,
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
        </div>
    );
}
