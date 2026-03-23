import type { FocusEvent, KeyboardEvent } from "react";
import { useCallback, useMemo, useRef, useState } from "react";
import { DndContext, DragOverlay, closestCenter } from "@dnd-kit/core";
import type { Task } from "@/features/tasks";
import {
    KANBAN_COLUMNS,
    type KanbanDependencyIndicatorsByTaskId,
    type KanbanLaneMode,
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
    laneMode: KanbanLaneMode;
    selectionMode: boolean;
    selectedTaskIds: Set<string>;
    onTaskClick: (taskId: string) => void;
    onSetColumnWipLimit: (column: TaskStatus, limit: number | null) => void;
}

interface TaskLocation {
    columnIndex: number;
    taskIndex: number;
}

function isEditableTarget(target: EventTarget | null): boolean {
    if (!(target instanceof HTMLElement)) return false;
    if (target.isContentEditable) return true;
    const tag = target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
    return target.closest("[contenteditable='true']") !== null;
}

function getFirstTaskId(tasksByStatus: Record<TaskStatus, Task[]>): string | null {
    for (const column of KANBAN_COLUMNS) {
        const first = tasksByStatus[column.id]?.[0];
        if (first) return first.id;
    }
    return null;
}

function getTaskLocation(
    tasksByStatus: Record<TaskStatus, Task[]>,
    taskId: string,
): TaskLocation | null {
    for (const [columnIndex, column] of KANBAN_COLUMNS.entries()) {
        const taskIndex = tasksByStatus[column.id].findIndex((task) => task.id === taskId);
        if (taskIndex >= 0) {
            return { columnIndex, taskIndex };
        }
    }
    return null;
}

export function KanbanBoard({
    tasksByStatus,
    allLeafTasksByStatus,
    allTasks,
    dependencyIndicatorsByTaskId,
    projectId,
    wipLimits,
    laneMode,
    selectionMode,
    selectedTaskIds,
    onTaskClick,
    onSetColumnWipLimit,
}: KanbanBoardProps) {
    const { sensors, activeTaskId, handleDragStart, handleDragCancel, handleDragEnd } =
        useKanbanDrag({ projectId, allTasks, allLeafTasksByStatus });
    const [focusedTaskId, setFocusedTaskId] = useState<string | null>(null);
    const [quickAddNonceByStatus, setQuickAddNonceByStatus] = useState<Partial<Record<TaskStatus, number>>>({});
    const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});

    const activeTask = activeTaskId
        ? Object.values(tasksByStatus)
              .flat()
              .find((t) => t.id === activeTaskId) ?? null
        : null;
    const orderedTaskIds = useMemo(
        () => KANBAN_COLUMNS.flatMap((column) => tasksByStatus[column.id].map((task) => task.id)),
        [tasksByStatus],
    );
    const resolvedFocusedTaskId = useMemo(() => {
        if (focusedTaskId && orderedTaskIds.includes(focusedTaskId)) {
            return focusedTaskId;
        }
        return orderedTaskIds[0] ?? null;
    }, [focusedTaskId, orderedTaskIds]);

    const focusTask = useCallback((taskId: string | null) => {
        if (!taskId) return;
        const node = cardRefs.current[taskId];
        if (!node) return;
        node.focus();
        setFocusedTaskId(taskId);
    }, []);

    const getCardRef = useCallback(
        (taskId: string) => (node: HTMLDivElement | null) => {
            cardRefs.current[taskId] = node;
        },
        [],
    );

    const triggerQuickAdd = useCallback((status: TaskStatus) => {
        setQuickAddNonceByStatus((current) => ({
            ...current,
            [status]: (current[status] ?? 0) + 1,
        }));
    }, []);

    const handleBoardFocus = useCallback((event: FocusEvent<HTMLDivElement>) => {
        if (event.target !== event.currentTarget) return;
        focusTask(resolvedFocusedTaskId ?? getFirstTaskId(tasksByStatus));
    }, [focusTask, resolvedFocusedTaskId, tasksByStatus]);

    const handleBoardKeyDown = useCallback((event: KeyboardEvent<HTMLDivElement>) => {
        if (isEditableTarget(event.target)) return;

        const key = event.key;
        if (key.toLowerCase() === "n" && !event.altKey && !event.ctrlKey && !event.metaKey) {
            event.preventDefault();
            const activeId = resolvedFocusedTaskId ?? getFirstTaskId(tasksByStatus);
            const location = activeId ? getTaskLocation(tasksByStatus, activeId) : null;
            const status = location ? KANBAN_COLUMNS[location.columnIndex].id : "BACKLOG";
            triggerQuickAdd(status);
            return;
        }

        if (key === "Enter" && resolvedFocusedTaskId) {
            event.preventDefault();
            onTaskClick(resolvedFocusedTaskId);
            return;
        }

        if (key !== "ArrowUp" && key !== "ArrowDown" && key !== "ArrowLeft" && key !== "ArrowRight") {
            return;
        }

        event.preventDefault();

        const activeId = resolvedFocusedTaskId ?? getFirstTaskId(tasksByStatus);
        if (!activeId) return;

        const location = getTaskLocation(tasksByStatus, activeId);
        if (!location) return;

        let nextTaskId: string | null = null;
        const currentColumn = KANBAN_COLUMNS[location.columnIndex];
        const currentTasks = tasksByStatus[currentColumn.id];

        if (key === "ArrowUp" || key === "ArrowDown") {
            const delta = key === "ArrowUp" ? -1 : 1;
            const nextIndex = location.taskIndex + delta;
            if (nextIndex >= 0 && nextIndex < currentTasks.length) {
                nextTaskId = currentTasks[nextIndex].id;
            }
        } else {
            const delta = key === "ArrowLeft" ? -1 : 1;
            let nextColumnIndex = location.columnIndex + delta;
            while (nextColumnIndex >= 0 && nextColumnIndex < KANBAN_COLUMNS.length) {
                const candidateTasks = tasksByStatus[KANBAN_COLUMNS[nextColumnIndex].id];
                if (candidateTasks.length > 0) {
                    nextTaskId = candidateTasks[Math.min(location.taskIndex, candidateTasks.length - 1)].id;
                    break;
                }
                nextColumnIndex += delta;
            }
        }

        focusTask(nextTaskId);
    }, [focusTask, onTaskClick, resolvedFocusedTaskId, tasksByStatus, triggerQuickAdd]);

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragCancel={handleDragCancel}
            onDragEnd={handleDragEnd}
        >
            <div
                className="flex flex-row gap-3 h-full overflow-x-auto overflow-y-hidden px-4 pb-4 focus:outline-none"
                tabIndex={0}
                onFocus={handleBoardFocus}
                onKeyDown={handleBoardKeyDown}
                aria-label="Kanban board"
            >
                {KANBAN_COLUMNS.map((col) => (
                    <KanbanColumn
                        key={col.id}
                        column={col}
                        tasks={tasksByStatus[col.id]}
                        dependencyIndicatorsByTaskId={dependencyIndicatorsByTaskId}
                        projectId={projectId}
                        wipLimit={wipLimits[col.id]}
                        laneMode={laneMode}
                        selectionMode={selectionMode}
                        selectedTaskIds={selectedTaskIds}
                        onTaskClick={onTaskClick}
                        onSetWipLimit={(limit) => onSetColumnWipLimit(col.id, limit)}
                        focusedTaskId={resolvedFocusedTaskId}
                        onCardFocus={setFocusedTaskId}
                        getCardRef={getCardRef}
                        quickAddNonce={quickAddNonceByStatus[col.id] ?? 0}
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
