import { format, parseISO } from "date-fns";
import {
    useReactTable,
    getCoreRowModel,
    flexRender,
    createColumnHelper,
} from "@tanstack/react-table";
import type { RowSelectionState, OnChangeFn } from "@tanstack/react-table";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/shared/ui/table";
import { Checkbox } from "@/shared/ui/checkbox";
import type { Task } from "@/features/tasks/types";
import { AddTaskRow } from "@/features/tasks/components/AddTaskRow";
import { TaskInlineEdit } from "@/features/tasks/components/TaskInlineEdit";
import { ChevronDown } from "lucide-react";

const columnHelper = createColumnHelper<Task>();

export const columns = [
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

            return (
                <div style={{ paddingLeft }} className="flex items-center gap-2 w-full">
                    {isSummary ? (
                        <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
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
];

interface TaskTableProps {
    projectId: string;
    data: Task[];
    rowSelection: RowSelectionState;
    setRowSelection: OnChangeFn<RowSelectionState>;
    forceAdding?: boolean;
    onCancelAdding?: () => void;
    onRowClick?: (taskId: string) => void;
}

export function TaskTable({
    projectId,
    data,
    rowSelection,
    setRowSelection,
    forceAdding,
    onCancelAdding,
    onRowClick
}: TaskTableProps) {
    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        onRowSelectionChange: setRowSelection,
        getRowId: (row) => row.id,
        state: {
            rowSelection,
        },
    });

    return (
        <Table>
            <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                            <TableHead key={header.id}>
                                {header.isPlaceholder
                                    ? null
                                    : flexRender(
                                        header.column.columnDef.header,
                                        header.getContext()
                                    )}
                            </TableHead>
                        ))}
                    </TableRow>
                ))}
            </TableHeader>
            <TableBody>
                {table.getRowModel().rows?.length ? (
                    table.getRowModel().rows.map((row) => (
                        <TableRow
                            key={row.id}
                            data-state={row.getIsSelected() && "selected"}
                            onClick={() => onRowClick?.(row.id)}
                            className="cursor-pointer"
                        >
                            {row.getVisibleCells().map((cell) => (
                                <TableCell key={cell.id}>
                                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                </TableCell>
                            ))}
                        </TableRow>
                    ))
                ) : (
                    <TableRow>
                        <TableCell colSpan={columns.length} className="h-24 text-center">
                            No tasks found. Create one below.
                        </TableCell>
                    </TableRow>
                )}

                {/* Inline Add Task Row */}
                <AddTaskRow
                    projectId={projectId}
                    colSpan={columns.length}
                    forceAdding={forceAdding}
                    onCancelAdding={onCancelAdding}
                />
            </TableBody>
        </Table>
    );
}
