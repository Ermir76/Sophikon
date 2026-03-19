import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import KanbanPage from "./KanbanPage";
import { useTasks } from "@/features/tasks";
import { useKanbanStore } from "../store/kanban-store";
import type { Task } from "@/features/tasks";
import type { TaskStatus } from "../types";

vi.mock("react-router", async () => {
    const actual = await vi.importActual<typeof import("react-router")>("react-router");
    return { ...actual, useParams: () => ({ projectId: "proj-1" }) };
});

vi.mock("@/features/tasks", () => ({
    useTasks: vi.fn(),
}));

vi.mock("../components/KanbanBoard", () => ({
    KanbanBoard: ({ tasksByStatus }: { tasksByStatus: Record<string, Task[]> }) => (
        <div data-testid="kanban-board">
            {Object.values(tasksByStatus)
                .flat()
                .map((t) => (
                    <div key={t.id}>{t.name}</div>
                ))}
        </div>
    ),
}));

vi.mock("../components/KanbanToolbar", () => ({
    KanbanToolbar: () => <div data-testid="kanban-toolbar" />,
}));

const baseTask = {
    project_id: "proj-1",
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
    is_milestone: false,
    is_critical: false,
    effort_driven: true,
    constraint_type: "ASAP",
    task_type: "FIXED_UNITS",
    actual_cost: 0,
    total_cost: 0,
    fixed_cost: 0,
    total_slack: 0,
    free_slack: 0,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
};

function makeTask(id: string, name: string, overrides: Partial<Task> = {}): Task {
    return {
        ...baseTask,
        id,
        name,
        status: "BACKLOG" as TaskStatus,
        is_summary: false,
        priority: 300,
        ...overrides,
    };
}

const leafTasks: Task[] = [
    makeTask("t1", "Deploy API", { priority: 800, status: "BACKLOG" }),
    makeTask("t2", "Write docs", { priority: 300, status: "TODO" }),
    makeTask("t3", "Authentication", { priority: 200, status: "IN_PROGRESS" }),
];

const summaryTask = makeTask("s1", "Phase 1 Summary", { is_summary: true });

function mockLoaded(tasks: Task[]) {
    vi.mocked(useTasks).mockReturnValue({
        data: { items: tasks, total: tasks.length },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
    } as never);
}

describe("KanbanPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useKanbanStore.setState({ collapsedByProject: {}, searchQuery: "", priorityFilter: "all" });
    });

    it("renders loading state", () => {
        vi.mocked(useTasks).mockReturnValue({
            isLoading: true,
            data: undefined,
            error: null,
            refetch: vi.fn(),
        } as never);
        render(<KanbanPage />);
        expect(screen.getByText("Loading tasks...")).toBeInTheDocument();
    });

    it("renders error state", () => {
        vi.mocked(useTasks).mockReturnValue({
            isLoading: false,
            data: undefined,
            error: new Error("fail"),
            refetch: vi.fn(),
        } as never);
        render(<KanbanPage />);
        expect(screen.getByText("Failed to load tasks.")).toBeInTheDocument();
    });

    it("renders board when data loads", () => {
        mockLoaded([...leafTasks, summaryTask]);
        render(<KanbanPage />);
        expect(screen.getByTestId("kanban-board")).toBeInTheDocument();
        expect(screen.getByText("Deploy API")).toBeInTheDocument();
        expect(screen.getByText("Write docs")).toBeInTheDocument();
        expect(screen.getByText("Authentication")).toBeInTheDocument();
    });

    it("filters out summary tasks", () => {
        mockLoaded([...leafTasks, summaryTask]);
        render(<KanbanPage />);
        expect(screen.queryByText("Phase 1 Summary")).not.toBeInTheDocument();
    });

    it("search filters tasks by name", () => {
        mockLoaded(leafTasks);
        useKanbanStore.getState().setSearch("deploy");
        render(<KanbanPage />);
        expect(screen.getByText("Deploy API")).toBeInTheDocument();
        expect(screen.queryByText("Write docs")).not.toBeInTheDocument();
        expect(screen.queryByText("Authentication")).not.toBeInTheDocument();
    });

    it("priority filter removes non-matching tasks", () => {
        mockLoaded(leafTasks);
        useKanbanStore.getState().setPriorityFilter("high");
        render(<KanbanPage />);
        // Only "Deploy API" has priority >= 750
        expect(screen.getByText("Deploy API")).toBeInTheDocument();
        expect(screen.queryByText("Write docs")).not.toBeInTheDocument();
        expect(screen.queryByText("Authentication")).not.toBeInTheDocument();
    });
});
