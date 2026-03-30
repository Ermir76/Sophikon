import { flexRender } from "@tanstack/react-table";
import type { Row, Cell } from "@tanstack/react-table";
import { TableRow, TableCell } from "@/shared/ui/table";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { Task } from "@/features/tasks/types";

export function SortableTableRow({ row }: { row: Row<Task> }) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: row.original.id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.8 : 1,
    };

    return (
        <TableRow
            ref={setNodeRef}
            style={style}
            data-state={row.getIsSelected() && "selected"}
            className={isDragging ? "bg-muted shadow-sm z-10 relative" : ""}
            onDoubleClick={() => row.table.options.meta?.onViewDetails?.(row.original.id)}
        >
            {row.getVisibleCells().map((cell: Cell<Task, unknown>) => (
                <TableCell
                    key={cell.id}
                    {...(cell.column.id === "drag-handle" ? { ...attributes, ...listeners } : {})}
                    className={`${cell.column.id === "drag-handle" ? "cursor-grab active:cursor-grabbing w-10 text-center" : ""} ${cell.column.id === "actions" ? "sticky right-0 bg-background z-10 w-12" : ""}`}
                >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
            ))}
        </TableRow>
    );
}
