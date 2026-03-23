import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { KanbanBoard } from "./KanbanBoard";
import { useKanbanStore } from "../store/kanban-store";
import type { Task } from "@/features/tasks";
import type { TaskStatus } from "../types";

vi.mock("@/features/tasks/hooks/useTasks", () => ({
    useCreateTask: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock("@dnd-kit/core", () => ({
    DndContext: ({ children }: { children: ReactNode }) => <>{children}</>,
    DragOverlay: ({ children }: { children: ReactNode }) => <>{children ?? null}</>,
    useSensors: () => [],
    useSensor: vi.fn(),
    PointerSensor: class {},
    useDroppable: () => ({ setNodeRef: vi.fn(), isOver: false }),
    useDraggable: () => ({ setNodeRef: vi.fn(), listeners: {}, attributes: {}, isDragging: false }),
}));

vi.mock("../hooks/useKanbanDrag", () => ({
    useKanbanDrag: () => ({
        sensors: [],
        activeTaskId: null,
        handleDragStart: vi.fn(),
        handleDragCancel: vi.fn(),
        handleDragEnd: vi.fn(),
    }),
}));

function makeEmptyBoard(): Record<TaskStatus, Task[]> {
    return { BACKLOG: [], TODO: [], IN_PROGRESS: [], IN_REVIEW: [], DONE: [] };
}

function makeTask(id: string, name: string, status: TaskStatus): Task {
    return {
        id,
        project_id: "proj-1",
        name,
        start_date: "2025-01-01",
        finish_date: "2030-12-31",
        duration: 480,
        work: 480,
        percent_complete: 0,
        percent_work_complete: 0,
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

describe("KanbanBoard", () => {
    beforeEach(() => {
        useKanbanStore.setState({
            collapsedByProject: {},
            searchQuery: "",
            priorityFilter: "all",
            selectedTaskId: null,
        });
    });

    it("renders all 5 column headers", () => {
        render(<KanbanBoard tasksByStatus={makeEmptyBoard()} projectId="proj-1" onTaskClick={vi.fn()} />);
        expect(screen.getByText("Backlog")).toBeInTheDocument();
        expect(screen.getByText("To Do")).toBeInTheDocument();
        expect(screen.getByText("In Progress")).toBeInTheDocument();
        expect(screen.getByText("In Review")).toBeInTheDocument();
        expect(screen.getByText("Done")).toBeInTheDocument();
    });

    it("renders tasks in their correct columns", () => {
        const board = makeEmptyBoard();
        board.BACKLOG = [makeTask("t1", "Write spec", "BACKLOG")];
        board.IN_PROGRESS = [makeTask("t2", "Implement API", "IN_PROGRESS")];
        board.DONE = [makeTask("t3", "Deploy v1", "DONE")];

        render(<KanbanBoard tasksByStatus={board} projectId="proj-1" onTaskClick={vi.fn()} />);
        expect(screen.getByText("Write spec")).toBeInTheDocument();
        expect(screen.getByText("Implement API")).toBeInTheDocument();
        expect(screen.getByText("Deploy v1")).toBeInTheDocument();
    });
});
