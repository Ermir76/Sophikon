import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { KanbanColumn } from "./KanbanColumn";
import { useKanbanStore } from "../store/kanban-store";
import type { Task } from "@/features/tasks";
import { TooltipProvider } from "@/shared/ui/tooltip";
import type { KanbanColumn as KanbanColumnType } from "../types";

const sortableContextSpy = vi.fn();

vi.mock("@dnd-kit/core", () => ({
    useDroppable: () => ({ setNodeRef: vi.fn(), isOver: false }),
}));

vi.mock("@dnd-kit/sortable", () => ({
    SortableContext: ({
        children,
        ...props
    }: {
        children: ReactNode;
        id: string;
        items: string[];
    }) => {
        sortableContextSpy(props);
        return <>{children}</>;
    },
    verticalListSortingStrategy: vi.fn(),
    useSortable: () => ({
        setNodeRef: vi.fn(),
        listeners: {},
        attributes: {},
        transform: null,
        transition: undefined,
        isDragging: false,
    }),
}));

vi.mock("@dnd-kit/utilities", () => ({
    CSS: {
        Transform: {
            toString: () => undefined,
        },
    },
}));

vi.mock("@/features/tasks/hooks/useTasks", () => ({
    useCreateTask: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

beforeEach(() => {
    useKanbanStore.setState({
        collapsedByProject: {},
        laneModeByProject: {},
        searchQuery: "",
        priorityFilter: "all",
        selectedTaskId: null,
        wipLimitsByProject: {},
    });
    sortableContextSpy.mockClear();
});

const backlogCol: KanbanColumnType = {
    id: "BACKLOG",
    label: "Backlog",
    color: "text-muted-foreground",
};

const makeTask = (id: string, name: string, overrides: Partial<Task> = {}): Task => ({
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
    ...overrides,
});

describe("KanbanColumn", () => {
    it("renders empty state when no tasks", () => {
        render(<KanbanColumn column={backlogCol} tasks={[]} dependencyIndicatorsByTaskId={{}} projectId="proj-1" laneMode="none" />);
        expect(screen.getByText("No tasks")).toBeInTheDocument();
    });

    it("renders task cards when tasks are provided", () => {
        const tasks = [makeTask("t1", "Deploy API"), makeTask("t2", "Write tests")];
        render(<KanbanColumn column={backlogCol} tasks={tasks} dependencyIndicatorsByTaskId={{}} projectId="proj-1" laneMode="none" />);
        expect(screen.getByText("Deploy API")).toBeInTheDocument();
        expect(screen.getByText("Write tests")).toBeInTheDocument();
    });

    it("renders column header with correct count", () => {
        const tasks = [makeTask("t1", "Task A"), makeTask("t2", "Task B")];
        render(<KanbanColumn column={backlogCol} tasks={tasks} dependencyIndicatorsByTaskId={{}} projectId="proj-1" laneMode="none" />);
        expect(screen.getByText("Backlog")).toBeInTheDocument();
        expect(screen.getByText("2")).toBeInTheDocument();
    });

    it("does not render 'No tasks' when tasks are present", () => {
        render(<KanbanColumn column={backlogCol} tasks={[makeTask("t1", "Task A")]} dependencyIndicatorsByTaskId={{}} projectId="proj-1" laneMode="none" />);
        expect(screen.queryByText("No tasks")).not.toBeInTheDocument();
    });

    it("shows warning indicator when task count exceeds WIP limit", () => {
        const tasks = [makeTask("t1", "Task A"), makeTask("t2", "Task B")];
        render(<KanbanColumn column={backlogCol} tasks={tasks} dependencyIndicatorsByTaskId={{}} projectId="proj-1" laneMode="none" wipLimit={1} />);
        expect(screen.getByText("2/1")).toBeInTheDocument();
        expect(screen.getByLabelText("Backlog WIP limit exceeded")).toBeInTheDocument();
    });

    it("groups cards by assignee lane with explicit unassigned bucket", () => {
        const assigned = makeTask("t1", "Assigned", {
            assignments: [{ resource_id: "r1", resource_name: "Alex Doe", resource_initials: "AD" }],
        });
        const unassigned = makeTask("t2", "No owner task");

        render(
            <TooltipProvider>
                <KanbanColumn
                    column={backlogCol}
                    tasks={[assigned, unassigned]}
                    dependencyIndicatorsByTaskId={{}}
                    projectId="proj-1"
                    laneMode="assignee"
                />
            </TooltipProvider>
        );

        expect(screen.getByText("Unassigned")).toBeInTheDocument();
        expect(screen.getByText("Alex Doe")).toBeInTheDocument();
    });

    it("groups cards by priority lane", () => {
        const high = makeTask("t1", "High", { priority: 900 });
        const minimal = makeTask("t2", "Minimal", { priority: 100 });

        render(
            <KanbanColumn
                column={backlogCol}
                tasks={[high, minimal]}
                dependencyIndicatorsByTaskId={{}}
                projectId="proj-1"
                laneMode="priority"
            />
        );

        expect(screen.getByText("High priority")).toBeInTheDocument();
        expect(screen.getByText("Minimal priority")).toBeInTheDocument();
    });

    it("keeps sortable drag context active when lane mode is enabled", () => {
        const assigned = makeTask("t1", "Assigned", {
            assignments: [{ resource_id: "r1", resource_name: "Alex Doe", resource_initials: "AD" }],
        });
        const unassigned = makeTask("t2", "No owner task");

        render(
            <TooltipProvider>
                <KanbanColumn
                    column={backlogCol}
                    tasks={[assigned, unassigned]}
                    dependencyIndicatorsByTaskId={{}}
                    projectId="proj-1"
                    laneMode="assignee"
                />
            </TooltipProvider>
        );

        expect(sortableContextSpy).toHaveBeenCalled();
        const latestCall = sortableContextSpy.mock.calls.at(-1)?.[0] as { id: string; items: string[] };
        expect(latestCall.id).toBe("BACKLOG");
        expect(latestCall.items).toEqual(["t1", "t2"]);
    });

    it("opens quick-add input when quickAddNonce increments", () => {
        const { rerender } = render(
            <KanbanColumn
                column={backlogCol}
                tasks={[makeTask("t1", "Task A")]}
                dependencyIndicatorsByTaskId={{}}
                projectId="proj-1"
                laneMode="none"
                quickAddNonce={0}
            />
        );

        expect(screen.queryByPlaceholderText("Task name...")).not.toBeInTheDocument();

        rerender(
            <KanbanColumn
                column={backlogCol}
                tasks={[makeTask("t1", "Task A")]}
                dependencyIndicatorsByTaskId={{}}
                projectId="proj-1"
                laneMode="none"
                quickAddNonce={1}
            />
        );

        expect(screen.getByPlaceholderText("Task name...")).toBeInTheDocument();
    });
});
