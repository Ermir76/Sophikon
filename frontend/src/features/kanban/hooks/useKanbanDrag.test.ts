import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useKanbanDrag } from "./useKanbanDrag";
import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";
import type { Task, TaskStatus } from "@/features/tasks";

const mockUpdateMutate = vi.fn();
const mockReorderMutate = vi.fn();

vi.mock("@/features/tasks", () => ({
    useUpdateTask: () => ({ mutate: mockUpdateMutate }),
    useReorderTask: () => ({ mutate: mockReorderMutate }),
}));
vi.mock("@/features/projects", () => ({
    useProject: () => ({ data: { settings: { status_thresholds: { IN_REVIEW: 70 } } } }),
}));

function makeTask(id: string, status: TaskStatus, parentTaskId?: string): Task {
    return {
        id,
        project_id: "proj-1",
        name: `Task ${id}`,
        start_date: "2025-01-01",
        finish_date: "2030-12-31",
        duration: 480,
        work: 480,
        percent_complete: 0,
        percent_work_complete: 0,
        parent_task_id: parentTaskId,
        wbs_code: "1.1",
        outline_level: 2,
        order_index: 1,
        sort_order: 1,
        is_summary: false,
        is_milestone: false,
        is_critical: false,
        effort_driven: true,
        priority: 300,
        constraint_type: "ASAP",
        task_type: "FIXED_UNITS",
        actual_cost: 0,
        total_cost: 0,
        fixed_cost: 0,
        total_slack: 0,
        free_slack: 0,
        status,
        created_at: "2025-01-01T00:00:00Z",
        updated_at: "2025-01-01T00:00:00Z",
    };
}

const task1 = makeTask("task-1", "BACKLOG");
const task2 = makeTask("task-2", "BACKLOG");
const task3 = makeTask("task-3", "TODO");
const summaryTask: Task = { ...makeTask("summary-1", "BACKLOG"), is_summary: true };

const allLeafTasksByStatus: Record<TaskStatus, Task[]> = {
    BACKLOG: [task1, task2],
    TODO: [task3],
    IN_PROGRESS: [],
    IN_REVIEW: [],
    DONE: [],
};

const allTasks: Task[] = [summaryTask, task1, task3, task2];

function makeDragStart(taskId: string, status: string): DragStartEvent {
    return {
        active: {
            id: taskId,
            data: { current: { status } },
            rect: { current: { initial: null, translated: null } },
        },
    } as unknown as DragStartEvent;
}

function makeDragEnd(
    taskId: string,
    currentStatus: string,
    overId: string | null,
    overStatus?: string,
): DragEndEvent {
    return {
        active: {
            id: taskId,
            data: { current: { status: currentStatus } },
            rect: { current: { initial: null, translated: null } },
        },
        over: overId
            ? { id: overId, data: { current: { status: overStatus } }, disabled: false, rect: {} as DOMRect }
            : null,
        delta: { x: 0, y: 0 },
        activatorEvent: {} as PointerEvent,
        collisions: [],
    } as unknown as DragEndEvent;
}

describe("useKanbanDrag", () => {
    beforeEach(() => {
        mockUpdateMutate.mockClear();
        mockReorderMutate.mockClear();
    });

    it("handleDragStart sets activeTaskId", () => {
        const { result } = renderHook(() => useKanbanDrag({
            projectId: "proj-1",
            allTasks,
            allLeafTasksByStatus: { ...allLeafTasksByStatus },
        }));

        act(() => {
            result.current.handleDragStart(makeDragStart("task-1", "BACKLOG"));
        });

        expect(result.current.activeTaskId).toBe("task-1");
    });

    it("handleDragEnd clears activeTaskId", () => {
        const { result } = renderHook(() => useKanbanDrag({
            projectId: "proj-1",
            allTasks,
            allLeafTasksByStatus: { ...allLeafTasksByStatus },
        }));

        act(() => {
            result.current.handleDragStart(makeDragStart("task-1", "BACKLOG"));
        });

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-1", "BACKLOG", "BACKLOG"));
        });

        expect(result.current.activeTaskId).toBeNull();
    });

    it("handleDragEnd calls updateTask when status changes", () => {
        const { result } = renderHook(() => useKanbanDrag({
            projectId: "proj-1",
            allTasks,
            allLeafTasksByStatus: { ...allLeafTasksByStatus },
        }));

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-1", "BACKLOG", "IN_PROGRESS"));
        });

        expect(mockUpdateMutate).toHaveBeenCalledWith(
            { taskId: "task-1", data: { status: "IN_PROGRESS", percent_complete: 1 } },
            expect.objectContaining({ onError: expect.any(Function) }),
        );
    });

    it("handleDragEnd reorders within same column and sends optimistic data", () => {
        const { result } = renderHook(() => useKanbanDrag({
            projectId: "proj-1",
            allTasks,
            allLeafTasksByStatus: { ...allLeafTasksByStatus },
        }));

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-2", "BACKLOG", "task-1", "BACKLOG"));
        });

        expect(mockReorderMutate).toHaveBeenCalledWith(
            {
                taskId: "task-2",
                data: { after_task_id: null, before_task_id: "task-1" },
                optimisticData: [
                    expect.objectContaining({ id: "summary-1" }),
                    expect.objectContaining({ id: "task-2" }),
                    expect.objectContaining({ id: "task-3" }),
                    expect.objectContaining({ id: "task-1" }),
                ],
            },
            expect.objectContaining({ onError: expect.any(Function) }),
        );
    });

    it("handleDragEnd does nothing when dropped on same column container", () => {
        const { result } = renderHook(() => useKanbanDrag({
            projectId: "proj-1",
            allTasks,
            allLeafTasksByStatus: { ...allLeafTasksByStatus },
        }));

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-1", "BACKLOG", "BACKLOG"));
        });

        expect(mockUpdateMutate).not.toHaveBeenCalled();
        expect(mockReorderMutate).not.toHaveBeenCalled();
    });

    it("handleDragEnd does nothing when over is null", () => {
        const { result } = renderHook(() => useKanbanDrag({
            projectId: "proj-1",
            allTasks,
            allLeafTasksByStatus: { ...allLeafTasksByStatus },
        }));

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-1", "BACKLOG", null));
        });

        expect(mockUpdateMutate).not.toHaveBeenCalled();
        expect(mockReorderMutate).not.toHaveBeenCalled();
    });

    it("handleDragEnd does not reorder across different parent groups", () => {
        const parentScopedTasks = {
            ...allLeafTasksByStatus,
            BACKLOG: [
                makeTask("task-1", "BACKLOG", "parent-a"),
                makeTask("task-2", "BACKLOG", "parent-b"),
            ],
        };
        const { result } = renderHook(() => useKanbanDrag({
            projectId: "proj-1",
            allTasks: [...allTasks],
            allLeafTasksByStatus: parentScopedTasks,
        }));

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-2", "BACKLOG", "task-1", "BACKLOG"));
        });

        expect(mockReorderMutate).not.toHaveBeenCalled();
    });

    it("handleDragCancel clears activeTaskId without calling updateTask", () => {
        const { result } = renderHook(() => useKanbanDrag({
            projectId: "proj-1",
            allTasks,
            allLeafTasksByStatus: { ...allLeafTasksByStatus },
        }));

        act(() => {
            result.current.handleDragStart(makeDragStart("task-1", "BACKLOG"));
        });
        expect(result.current.activeTaskId).toBe("task-1");

        act(() => {
            result.current.handleDragCancel();
        });

        expect(result.current.activeTaskId).toBeNull();
        expect(mockUpdateMutate).not.toHaveBeenCalled();
        expect(mockReorderMutate).not.toHaveBeenCalled();
    });
});
