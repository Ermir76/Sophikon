import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { KanbanColumn } from "./KanbanColumn";
import { useKanbanStore } from "../store/kanban-store";
import type { Task } from "@/features/tasks";
import type { KanbanColumn as KanbanColumnType } from "../types";

vi.mock("@dnd-kit/core", () => ({
    useDroppable: () => ({ setNodeRef: vi.fn(), isOver: false }),
    useDraggable: () => ({ setNodeRef: vi.fn(), listeners: {}, attributes: {}, isDragging: false }),
}));

vi.mock("@/features/tasks/hooks/useTasks", () => ({
    useCreateTask: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

beforeEach(() => {
    useKanbanStore.setState({
        collapsedByProject: {},
        searchQuery: "",
        priorityFilter: "all",
        selectedTaskId: null,
        wipLimitsByProject: {},
    });
});

const backlogCol: KanbanColumnType = {
    id: "BACKLOG",
    label: "Backlog",
    color: "text-muted-foreground",
};

const makeTask = (id: string, name: string): Task => ({
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
    status: "BACKLOG",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
});

describe("KanbanColumn", () => {
    it("renders empty state when no tasks", () => {
        render(<KanbanColumn column={backlogCol} tasks={[]} projectId="proj-1" />);
        expect(screen.getByText("No tasks")).toBeInTheDocument();
    });

    it("renders task cards when tasks are provided", () => {
        const tasks = [makeTask("t1", "Deploy API"), makeTask("t2", "Write tests")];
        render(<KanbanColumn column={backlogCol} tasks={tasks} projectId="proj-1" />);
        expect(screen.getByText("Deploy API")).toBeInTheDocument();
        expect(screen.getByText("Write tests")).toBeInTheDocument();
    });

    it("renders column header with correct count", () => {
        const tasks = [makeTask("t1", "Task A"), makeTask("t2", "Task B")];
        render(<KanbanColumn column={backlogCol} tasks={tasks} projectId="proj-1" />);
        expect(screen.getByText("Backlog")).toBeInTheDocument();
        expect(screen.getByText("2")).toBeInTheDocument();
    });

    it("does not render 'No tasks' when tasks are present", () => {
        render(<KanbanColumn column={backlogCol} tasks={[makeTask("t1", "Task A")]} projectId="proj-1" />);
        expect(screen.queryByText("No tasks")).not.toBeInTheDocument();
    });

    it("shows warning indicator when task count exceeds WIP limit", () => {
        const tasks = [makeTask("t1", "Task A"), makeTask("t2", "Task B")];
        render(<KanbanColumn column={backlogCol} tasks={tasks} projectId="proj-1" wipLimit={1} />);
        expect(screen.getByText("2/1")).toBeInTheDocument();
        expect(screen.getByLabelText("Backlog WIP limit exceeded")).toBeInTheDocument();
    });
});
