import {
    useReactTable,
    getCoreRowModel,
    flexRender,
} from "@tanstack/react-table";
import type { RowSelectionState, OnChangeFn, Row } from "@tanstack/react-table";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/shared/ui/table";
import type { Task } from "@/features/tasks/types";
import { AddTaskRow } from "@/features/tasks/components/task-table/AddTaskRow";
import { taskColumns } from "@/features/tasks/components/task-table/TaskTableColumns";
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
} from "@dnd-kit/core";
import type { DragEndEvent } from "@dnd-kit/core";
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
    useSortable,
} from "@dnd-kit/sortable";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import { CSS } from "@dnd-kit/utilities";

interface TaskTableProps {
    projectId: string;
    data: Task[];
    rowSelection: RowSelectionState;
    setRowSelection: OnChangeFn<RowSelectionState>;
    forceAdding?: boolean;
    onCancelAdding?: () => void;
    onRowClick?: (taskId: string) => void;
    onReorder?: (taskId: string, afterTaskId?: string, beforeTaskId?: string, sortedData?: Task[]) => void;
}

interface SortableTableRowProps {
    row: Row<Task>;
    onRowClick?: (id: string) => void;
}

function SortableTableRow({ row, onRowClick }: SortableTableRowProps) {
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
            onClick={() => onRowClick?.(row.original.id)}
            className={`cursor-pointer ${isDragging ? "bg-muted shadow-sm z-10 relative" : ""}`}
        >
            {row.getVisibleCells().map((cell: any) => (
                <TableCell
                    key={cell.id}
                    {...(cell.column.id === "drag-handle" ? { ...attributes, ...listeners } : {})}
                    className={cell.column.id === "drag-handle" ? "cursor-grab active:cursor-grabbing w-10 text-center" : ""}
                >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
            ))}
        </TableRow>
    );
}

export function TaskTable({
    projectId,
    data,
    rowSelection,
    setRowSelection,
    forceAdding,
    onCancelAdding,
    onRowClick,
    onReorder
}: TaskTableProps) {
    const table = useReactTable({
        data,
        columns: taskColumns,
        getCoreRowModel: getCoreRowModel(),
        onRowSelectionChange: setRowSelection,
        getRowId: (row) => row.id,
        state: {
            rowSelection,
        },
    });

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: { distance: 5 },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            const oldIndex = data.findIndex((item) => item.id === active.id);
            const newIndex = data.findIndex((item) => item.id === over.id);

            const sortedData = arrayMove(data, oldIndex, newIndex);

            let afterTaskId = undefined;
            let beforeTaskId = undefined;

            if (newIndex > 0) afterTaskId = sortedData[newIndex - 1].id;
            if (newIndex < sortedData.length - 1) beforeTaskId = sortedData[newIndex + 1].id;

            onReorder?.(active.id as string, afterTaskId, beforeTaskId, sortedData);
        }
    };

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            modifiers={[restrictToVerticalAxis]}
            onDragEnd={handleDragEnd}
        >
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
                    <SortableContext
                        items={data.map((t) => t.id)}
                        strategy={verticalListSortingStrategy}
                    >
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <SortableTableRow
                                    key={row.id}
                                    row={row}
                                    onRowClick={onRowClick}
                                />
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={taskColumns.length} className="h-24 text-center">
                                    No tasks found. Create one below.
                                </TableCell>
                            </TableRow>
                        )}
                    </SortableContext>

                    {/* Inline Add Task Row */}
                    <AddTaskRow
                        projectId={projectId}
                        colSpan={taskColumns.length}
                        forceAdding={forceAdding}
                        onCancelAdding={onCancelAdding}
                    />
                </TableBody>
            </Table>
        </DndContext>
    );
}
