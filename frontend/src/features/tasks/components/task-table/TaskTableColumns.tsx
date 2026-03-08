import { format, isValid, parseISO, startOfDay } from "date-fns";
import { createColumnHelper, type RowData } from "@tanstack/react-table";
import { Checkbox } from "@/shared/ui/checkbox";
import { Badge } from "@/shared/ui/badge";
import type { Task } from "@/features/tasks/types";
import { TaskInlineEdit } from "@/features/tasks/components/task-table/TaskInlineEdit";
import { TaskRowActions } from "@/features/tasks/components/task-table/TaskRowActions";
import { ChevronDown, ChevronRight, GripVertical, MessageSquare } from "lucide-react";

declare module "@tanstack/react-table" {
    interface TableMeta<TData extends RowData> {
        collapsedTaskIds?: Set<string>;
        toggleTaskCollapse?: (taskId: string) => void;
        onIndent?: (taskId: string) => void;
        onOutdent?: (taskId: string) => void;
        onAddDependency?: (taskId: string) => void;
        onViewDetails?: (taskId: string) => void;
        onDelete?: (taskId: string) => void;
        isIndentPending?: boolean;
        isOutdentPending?: boolean;
        isDeletePending?: boolean;
    }
}

const columnHelper = createColumnHelper<Task>();

function isPastDueDate(dateValue: string, now: Date): boolean {
    const parsed = parseISO(dateValue);
    if (!isValid(parsed)) return false;
    return parsed < startOfDay(now);
}

function getTaskStatus(task: Task): "completed" | "overdue" | "in-progress" | "not-started" {
    const now = new Date();
    if (task.percent_complete >= 100) return "completed";
    if (task.finish_date && isPastDueDate(task.finish_date, now)) return "overdue";
    if (task.percent_complete > 0) return "in-progress";
    return "not-started";
}

function getPriorityLabel(priority: number): "High" | "Medium" | "Low" {
    if (priority >= 700) return "High";
    if (priority >= 400) return "Medium";
    return "Low";
}

export const taskColumns = [
    columnHelper.display({
        id: "drag-handle",
        header: "",
        cell: () => (
            <div className="flex items-center justify-center text-muted-foreground">
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
    columnHelper.display({
        id: "comments",
        header: "Comments",
        cell: (info) => (
            <div className="flex items-center gap-1 text-muted-foreground">
                <MessageSquare className="size-4" />
                <span>{info.row.original.comments_count ?? 0}</span>
            </div>
        ),
    }),
    columnHelper.display({
        id: "status",
        header: "Status",
        cell: (info) => {
            const status = getTaskStatus(info.row.original);
            if (status === "completed") {
                return (
                    <Badge variant="outline" className="border-emerald-500/45 bg-emerald-500/12 text-emerald-600 dark:text-emerald-400">
                        Completed
                    </Badge>
                );
            }
            if (status === "overdue") {
                return (
                    <Badge variant="outline" className="border-destructive/45 bg-destructive/12 text-destructive">
                        Overdue
                    </Badge>
                );
            }
            if (status === "in-progress") {
                return (
                    <Badge variant="outline" className="border-primary/45 bg-primary/12 text-primary">
                        In Progress
                    </Badge>
                );
            }
            return (
                <Badge variant="outline" className="border-muted-foreground/30 bg-muted/35 text-muted-foreground">
                    Not Started
                </Badge>
            );
        },
    }),
    columnHelper.accessor("priority", {
        header: "Priority",
        cell: (info) => {
            const label = getPriorityLabel(Number(info.getValue() ?? 0));
            const className =
                label === "High"
                    ? "border-destructive/45 bg-destructive/10 text-destructive"
                    : label === "Medium"
                        ? "border-chart-3/45 bg-chart-3/12 text-chart-3"
                        : "border-primary/40 bg-primary/10 text-primary";
            return (
                <Badge variant="outline" className={className}>
                    {label}
                </Badge>
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
        cell: (info) => info.getValue() ? format(parseISO(info.getValue()), "MMM d, yyyy") : "-",
    }),
    columnHelper.accessor("finish_date", {
        header: "Finish",
        cell: (info) => info.getValue() ? format(parseISO(info.getValue()), "MMM d, yyyy") : "-",
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
                    onDelete={meta?.onDelete}
                    isIndentPending={meta?.isIndentPending}
                    isOutdentPending={meta?.isOutdentPending}
                    isDeletePending={meta?.isDeletePending}
                />
            );
        },
    }),
];
