import {
    useReactTable,
    getCoreRowModel,
    flexRender,
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
import type { Task } from "@/features/tasks/types";
import { AddTaskRow } from "@/features/tasks/components/task-table/AddTaskRow";
import { SortableTableRow } from "@/features/tasks/components/task-table/SortableTableRow";
import { taskColumns } from "@/features/tasks/components/task-table/TaskTableColumns";
import { useCollapsedTasks } from "@/features/tasks/hooks/useCollapsedTasks";
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
} from "@dnd-kit/sortable";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";

interface TaskTableProps {
    projectId: string;
    data: Task[];
    rowSelection: RowSelectionState;
    setRowSelection: OnChangeFn<RowSelectionState>;
    forceAdding?: boolean;
    onCancelAdding?: () => void;
    onReorder?: (taskId: string, afterTaskId?: string, beforeTaskId?: string, sortedData?: Task[]) => void;
    onIndent?: (taskId: string) => void;
    onOutdent?: (taskId: string) => void;
    onAddDependency?: (taskId: string) => void;
    onViewDetails?: (taskId: string) => void;
    onDelete?: (taskId: string) => void;
    isIndentPending?: boolean;
    isOutdentPending?: boolean;
    isDeletePending?: boolean;
}

export function TaskTable({
    projectId,
    data,
    rowSelection,
    setRowSelection,
    forceAdding,
    onCancelAdding,
    onReorder,
    onIndent,
    onOutdent,
    onAddDependency,
    onViewDetails,
    onDelete,
    isIndentPending,
    isOutdentPending,
    isDeletePending,
}: TaskTableProps) {
    const { visibleData, collapsedTaskIds, toggleTaskCollapse } = useCollapsedTasks(projectId, data);

    const table = useReactTable({
        data: visibleData,
        columns: taskColumns,
        getCoreRowModel: getCoreRowModel(),
        onRowSelectionChange: setRowSelection,
        getRowId: (row) => row.id,
        state: { rowSelection },
        meta: {
            collapsedTaskIds,
            toggleTaskCollapse,
            onIndent,
            onOutdent,
            onAddDependency,
            onViewDetails,
            onDelete,
            isIndentPending,
            isOutdentPending,
            isDeletePending,
        },
    });

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
        useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            const oldIndex = visibleData.findIndex((item) => item.id === active.id);
            const newIndex = visibleData.findIndex((item) => item.id === over.id);
            const sortedData = arrayMove(visibleData, oldIndex, newIndex);

            let afterTaskId = undefined;
            if (newIndex > 0) afterTaskId = sortedData[newIndex - 1].id;

            onReorder?.(active.id as string, afterTaskId, undefined, sortedData);
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
                    <SortableContext
                        items={visibleData.map((t) => t.id)}
                        strategy={verticalListSortingStrategy}
                    >
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <SortableTableRow key={row.id} row={row} />
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={taskColumns.length} className="h-24 text-center">
                                    No tasks found. Create one below.
                                </TableCell>
                            </TableRow>
                        )}
                    </SortableContext>

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
