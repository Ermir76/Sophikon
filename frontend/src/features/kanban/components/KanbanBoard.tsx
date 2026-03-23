import { DndContext, DragOverlay, closestCenter } from "@dnd-kit/core";
import type { Task } from "@/features/tasks";
import {
    KANBAN_COLUMNS,
    type KanbanDependencyIndicatorsByTaskId,
    type KanbanWipLimits,
    type TaskStatus,
} from "../types";
import { KanbanColumn } from "./KanbanColumn";
import { KanbanCard } from "./KanbanCard";
import { useKanbanDrag } from "../hooks/useKanbanDrag";

interface KanbanBoardProps {
    tasksByStatus: Record<TaskStatus, Task[]>;
    allLeafTasksByStatus: Record<TaskStatus, Task[]>;
    allTasks: Task[];
    dependencyIndicatorsByTaskId: KanbanDependencyIndicatorsByTaskId;
    projectId: string | undefined;
    wipLimits: KanbanWipLimits;
    onTaskClick: (taskId: string) => void;
    onSetColumnWipLimit: (column: TaskStatus, limit: number | null) => void;
}

export function KanbanBoard({
    tasksByStatus,
    allLeafTasksByStatus,
    allTasks,
    dependencyIndicatorsByTaskId,
    projectId,
    wipLimits,
    onTaskClick,
    onSetColumnWipLimit,
}: KanbanBoardProps) {
    const { sensors, activeTaskId, handleDragStart, handleDragCancel, handleDragEnd } =
        useKanbanDrag({ projectId, allTasks, allLeafTasksByStatus });

    const activeTask = activeTaskId
        ? Object.values(tasksByStatus)
              .flat()
              .find((t) => t.id === activeTaskId) ?? null
        : null;

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragCancel={handleDragCancel}
            onDragEnd={handleDragEnd}
        >
            <div className="flex flex-row gap-3 h-full overflow-x-auto overflow-y-hidden px-4 pb-4">
                {KANBAN_COLUMNS.map((col) => (
                    <KanbanColumn
                        key={col.id}
                        column={col}
                        tasks={tasksByStatus[col.id]}
                        dependencyIndicatorsByTaskId={dependencyIndicatorsByTaskId}
                        projectId={projectId}
                        wipLimit={wipLimits[col.id]}
                        onTaskClick={onTaskClick}
                        onSetWipLimit={(limit) => onSetColumnWipLimit(col.id, limit)}
                    />
                ))}
            </div>
            <DragOverlay>
                {activeTask && (
                    <KanbanCard
                        task={activeTask}
                        dependencyIndicator={dependencyIndicatorsByTaskId[activeTask.id]}
                        isDragOverlay
                    />
                )}
            </DragOverlay>
        </DndContext>
    );
}
