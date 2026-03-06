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
        <div className="overflow-hidden rounded-lg border bg-card/70">
            <Table>
                <TableHeader className="sticky top-0 z-20 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">
                    {table.getHeaderGroups().map((headerGroup) => (
                        <TableRow key={headerGroup.id}>
                            {headerGroup.headers.map((header) => (
                                <TableHead
                                    key={header.id}
                                    className={header.id === "actions" ? "sticky right-0 z-10 w-12 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85" : ""}
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
        </div>
    );
}
