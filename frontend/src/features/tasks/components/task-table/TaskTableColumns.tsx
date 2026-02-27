import { format, parseISO } from "date-fns";
import { createColumnHelper } from "@tanstack/react-table";
import { Checkbox } from "@/shared/ui/checkbox";
import type { Task } from "@/features/tasks/types";
import { TaskInlineEdit } from "@/features/tasks/components/task-table/TaskInlineEdit";
import { TaskRowActions } from "@/features/tasks/components/task-table/TaskRowActions";
import { ChevronDown, ChevronRight, GripVertical } from "lucide-react";

declare module "@tanstack/react-table" {
    interface TableMeta<TData> {
        collapsedTaskIds?: Set<string>;
        toggleTaskCollapse?: (taskId: string) => void;
        onIndent?: (taskId: string) => void;
        onOutdent?: (taskId: string) => void;
        onAddDependency?: (taskId: string) => void;
        onViewDetails?: (taskId: string) => void;
        isIndentPending?: boolean;
        isOutdentPending?: boolean;
    }
}

const columnHelper = createColumnHelper<Task>();

export const taskColumns = [
    columnHelper.display({
        id: "drag-handle",
        header: "",
        cell: () => (
            <div className="flex items-center justify-center text-muted-foreground/50 hover:text-foreground">
                <GripVertical className="size-4" />
            </div>
        ),
    }),
    columnHelper.display({
        id: "select",
        header: ({ table }) => (
            <div onClick={(e) => e.stopPropagation()} className="flex items-center justify-center">
                <Checkbox
                    checked={
                        table.getIsAllPageRowsSelected() ||
                        (table.getIsSomePageRowsSelected() && "indeterminate")
                    }
                    onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                    aria-label="Select all"
                />
            </div>
        ),
        cell: ({ row }) => (
            <div onClick={(e) => e.stopPropagation()} className="flex items-center justify-center">
                <Checkbox
                    checked={row.getIsSelected()}
                    onCheckedChange={(value) => row.toggleSelected(!!value)}
                    aria-label="Select row"
                />
            </div>
        ),
    }),
    columnHelper.accessor("wbs_code", {
        header: "WBS",
        cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("name", {
        header: "Task Name",
        cell: (info) => {
            const task = info.row.original;
            // Visual indentation based on outline_level
            const paddingLeft = `${(task.outline_level - 1) * 20}px`;
            const isSummary = task.is_summary;
            const meta = info.table.options.meta;
            const isCollapsed = meta?.collapsedTaskIds?.has(task.id);

            return (
                <div style={{ paddingLeft }} className="flex items-center gap-2 w-full">
                    {isSummary ? (
                        <div
                            className="cursor-pointer hover:bg-muted rounded-sm p-0.5"
                            onClick={(e) => {
                                e.stopPropagation();
                                meta?.toggleTaskCollapse?.(task.id);
                            }}
                        >
                            {isCollapsed ? (
                                <ChevronRight className="size-4 shrink-0 text-muted-foreground transition-transform" />
                            ) : (
                                <ChevronDown className="size-4 shrink-0 text-muted-foreground transition-transform" />
                            )}
                        </div>
                    ) : (
                        <div className="size-4 shrink-0" /> // Placeholder for alignment
                    )}
                    <span className={`w-full ${isSummary ? "font-bold" : ""}`}>
                        <TaskInlineEdit
                            task={task}
                            field="name"
                            value={info.getValue()}
                            type="text"
                        />
                    </span>
                </div>
            );
        },
    }),
    columnHelper.accessor("duration", {
        header: "Duration",
        cell: (info) => (
            <div className="flex items-center gap-1">
                <TaskInlineEdit
                    task={info.row.original}
                    field="duration"
                    value={info.getValue()}
                    type="number"
                    disabled={info.row.original.is_summary}
                />
                <span className="text-muted-foreground shrink-0 text-xs">mins</span>
            </div>
        ),
    }),
    columnHelper.accessor("start_date", {
        header: "Start",
        cell: (info) => info.getValue() ? format(parseISO(info.getValue()), "MMM d, yyyy") : "—",
    }),
    columnHelper.accessor("finish_date", {
        header: "Finish",
        cell: (info) => info.getValue() ? format(parseISO(info.getValue()), "MMM d, yyyy") : "—",
    }),
    columnHelper.accessor("percent_complete", {
        header: "% Complete",
        cell: (info) => `${info.getValue()}%`,
    }),
    columnHelper.display({
        id: "actions",
        header: "",
        cell: (info) => {
            const task = info.row.original;
            const meta = info.table.options.meta;
            return (
                <TaskRowActions
                    task={task}
                    onIndent={meta?.onIndent}
                    onOutdent={meta?.onOutdent}
                    onAddDependency={meta?.onAddDependency}
                    onViewDetails={meta?.onViewDetails}
                    isIndentPending={meta?.isIndentPending}
                    isOutdentPending={meta?.isOutdentPending}
                />
            );
        },
    }),
];
