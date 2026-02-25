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
import { ChevronDown } from "lucide-react";

const columnHelper = createColumnHelper<Task>();

export const columns = [
    columnHelper.display({
        id: "select",
        header: ({ table }) => (
            <Checkbox
                checked={
                    table.getIsAllPageRowsSelected() ||
                    (table.getIsSomePageRowsSelected() && "indeterminate")
                }
                onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                aria-label="Select all"
            />
        ),
        cell: ({ row }) => (
            <Checkbox
                checked={row.getIsSelected()}
                onCheckedChange={(value) => row.toggleSelected(!!value)}
                aria-label="Select row"
            />
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
                <div style={{ paddingLeft }} className="flex items-center gap-2">
                    {isSummary ? (
                        <ChevronDown className="size-4 text-muted-foreground" />
                    ) : (
                        <div className="size-4" /> // Placeholder for alignment
                    )}
                    <span className={isSummary ? "font-bold" : ""}>
                        {info.getValue()}
                    </span>
                </div>
            );
        },
    }),
    columnHelper.accessor("duration", {
        header: "Duration",
        cell: (info) => `${info.getValue()} mins`,
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
    data: Task[];
    rowSelection: RowSelectionState;
    setRowSelection: OnChangeFn<RowSelectionState>;
}

export function TaskTable({ data, rowSelection, setRowSelection }: TaskTableProps) {
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
                            No tasks found.
                        </TableCell>
                    </TableRow>
                )}
            </TableBody>
        </Table>
    );
}
