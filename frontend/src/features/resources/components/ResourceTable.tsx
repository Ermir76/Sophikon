import {
    useReactTable,
    getCoreRowModel,
    flexRender,
    type RowSelectionState,
    type OnChangeFn,
} from "@tanstack/react-table";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/shared/ui/table";
import { resourceColumns } from "@/features/resources/components/ResourceTableColumns";
import type { Resource } from "@/features/resources/types";

interface ResourceTableProps {
    data: Resource[];
    rowSelection: RowSelectionState;
    setRowSelection: OnChangeFn<RowSelectionState>;
    onViewDetails?: (resourceId: string) => void;
    onDelete?: (resourceId: string) => void;
    isDeletePending?: boolean;
    overAllocatedResourceIds?: Set<string>;
}

export function ResourceTable({
    data,
    rowSelection,
    setRowSelection,
    onViewDetails,
    onDelete,
    isDeletePending,
    overAllocatedResourceIds,
}: ResourceTableProps) {
    const table = useReactTable({
        data,
        columns: resourceColumns,
        getCoreRowModel: getCoreRowModel(),
        getRowId: (row) => row.id,
        onRowSelectionChange: setRowSelection,
        state: { rowSelection },
        meta: {
            onViewDetails,
            onDeleteResource: onDelete,
            isDeleteResourcePending: isDeletePending,
            overAllocatedResourceIds,
        },
    });

    return (
        <Table>
            <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                            <TableHead
                                key={header.id}
                                className={header.id === "actions" ? "sticky right-0 bg-background z-10 w-12" : ""}
                            >
                                {header.isPlaceholder
                                    ? null
                                    : flexRender(header.column.columnDef.header, header.getContext())}
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
                            className="cursor-pointer"
                            onClick={() => onViewDetails?.(row.original.id)}
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
                        <TableCell colSpan={resourceColumns.length} className="h-24 text-center">
                            No resources found.
                        </TableCell>
                    </TableRow>
                )}
            </TableBody>
        </Table>
    );
}
