import { DndContext, DragOverlay } from "@dnd-kit/core";
import type { Task } from "@/features/tasks";
import { KANBAN_COLUMNS, type TaskStatus } from "../types";
import { KanbanColumn } from "./KanbanColumn";
import { KanbanCard } from "./KanbanCard";
import { useKanbanDrag } from "../hooks/useKanbanDrag";

interface KanbanBoardProps {
    tasksByStatus: Record<TaskStatus, Task[]>;
    projectId: string | undefined;
    onTaskClick: (taskId: string) => void;
}

export function KanbanBoard({ tasksByStatus, projectId, onTaskClick }: KanbanBoardProps) {
    const { sensors, activeTaskId, handleDragStart, handleDragCancel, handleDragEnd } =
        useKanbanDrag(projectId);

    const activeTask = activeTaskId
        ? Object.values(tasksByStatus)
              .flat()
              .find((t) => t.id === activeTaskId) ?? null
        : null;

    return (
        <DndContext
            sensors={sensors}
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
                        projectId={projectId}
                        onTaskClick={onTaskClick}
                    />
                ))}
            </div>
            <DragOverlay>
                {activeTask && <KanbanCard task={activeTask} isDragOverlay />}
            </DragOverlay>
        </DndContext>
    );
}
