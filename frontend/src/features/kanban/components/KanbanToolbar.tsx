import { Search } from "lucide-react";
import { Input } from "@/shared/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/shared/ui/select";
import type { PriorityFilter } from "../types";

export type { PriorityFilter };

interface KanbanToolbarProps {
    searchQuery: string;
    onSearchChange: (value: string) => void;
    priorityFilter: PriorityFilter;
    onPriorityFilterChange: (value: PriorityFilter) => void;
}

export function KanbanToolbar({
    searchQuery,
    onSearchChange,
    priorityFilter,
    onPriorityFilterChange,
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
                    <SelectItem value="high">High (≥ 750)</SelectItem>
                    <SelectItem value="medium">Medium (≥ 500)</SelectItem>
                    <SelectItem value="low">Low (≥ 250)</SelectItem>
                    <SelectItem value="minimal">Minimal</SelectItem>
                </SelectContent>
            </Select>
        </div>
    );
}
