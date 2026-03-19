import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useKanbanDrag } from "./useKanbanDrag";
import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";

const mockMutate = vi.fn();

vi.mock("@/features/tasks", () => ({
    useUpdateTask: () => ({ mutate: mockMutate }),
}));

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
): DragEndEvent {
    return {
        active: {
            id: taskId,
            data: { current: { status: currentStatus } },
            rect: { current: { initial: null, translated: null } },
        },
        over: overId
            ? { id: overId, data: { current: {} }, disabled: false, rect: {} as DOMRect }
            : null,
        delta: { x: 0, y: 0 },
        activatorEvent: {} as PointerEvent,
        collisions: [],
    } as unknown as DragEndEvent;
}

describe("useKanbanDrag", () => {
    beforeEach(() => {
        mockMutate.mockClear();
    });

    it("handleDragStart sets activeTaskId", () => {
        const { result } = renderHook(() => useKanbanDrag("proj-1"));

        act(() => {
            result.current.handleDragStart(makeDragStart("task-1", "BACKLOG"));
        });

        expect(result.current.activeTaskId).toBe("task-1");
    });

    it("handleDragEnd clears activeTaskId", () => {
        const { result } = renderHook(() => useKanbanDrag("proj-1"));

        act(() => {
            result.current.handleDragStart(makeDragStart("task-1", "BACKLOG"));
        });

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-1", "BACKLOG", "BACKLOG"));
        });

        expect(result.current.activeTaskId).toBeNull();
    });

    it("handleDragEnd calls updateTask when status changes", () => {
        const { result } = renderHook(() => useKanbanDrag("proj-1"));

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-1", "BACKLOG", "IN_PROGRESS"));
        });

        expect(mockMutate).toHaveBeenCalledWith({
            taskId: "task-1",
            data: { status: "IN_PROGRESS" },
        });
    });

    it("handleDragEnd does nothing when dropped on the same column", () => {
        const { result } = renderHook(() => useKanbanDrag("proj-1"));

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-1", "BACKLOG", "BACKLOG"));
        });

        expect(mockMutate).not.toHaveBeenCalled();
    });

    it("handleDragEnd does nothing when over is null", () => {
        const { result } = renderHook(() => useKanbanDrag("proj-1"));

        act(() => {
            result.current.handleDragEnd(makeDragEnd("task-1", "BACKLOG", null));
        });

        expect(mockMutate).not.toHaveBeenCalled();
    });

    it("handleDragCancel clears activeTaskId without calling updateTask", () => {
        const { result } = renderHook(() => useKanbanDrag("proj-1"));

        act(() => {
            result.current.handleDragStart(makeDragStart("task-1", "BACKLOG"));
        });
        expect(result.current.activeTaskId).toBe("task-1");

        act(() => {
            result.current.handleDragCancel();
        });

        expect(result.current.activeTaskId).toBeNull();
        expect(mockMutate).not.toHaveBeenCalled();
    });
});
