import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import KanbanPage from "./KanbanPage";
import { useProject, useUpdateProject } from "@/features/projects";
import { useBulkUpdateTasks, useDependencies, useTasks } from "@/features/tasks";
import { useKanbanStore } from "../store/kanban-store";
import type { Task } from "@/features/tasks";
import type { TaskStatus } from "../types";

vi.mock("react-router", async () => {
    const actual = await vi.importActual<typeof import("react-router")>("react-router");
    return { ...actual, useParams: () => ({ projectId: "proj-1" }) };
});

vi.mock("@/features/tasks", () => ({
    useTasks: vi.fn(),
    useDependencies: vi.fn(),
    useBulkUpdateTasks: vi.fn(),
    TaskDetailPanel: ({ isOpen }: { isOpen: boolean }) =>
        isOpen ? <div data-testid="task-detail-panel">task detail</div> : null,
}));

vi.mock("@/features/projects", () => ({
    useProject: vi.fn(),
    useUpdateProject: vi.fn(),
}));

vi.mock("../components/KanbanBoard", () => ({
    KanbanBoard: ({
        tasksByStatus,
        dependencyIndicatorsByTaskId,
        laneMode,
        selectionMode,
        selectedTaskIds,
        onTaskClick,
        onSetColumnWipLimit,
    }: {
        tasksByStatus: Record<string, Task[]>;
        dependencyIndicatorsByTaskId: Record<string, { blockedCount: number; blockingCount: number }>;
        laneMode: "none" | "assignee" | "priority";
        selectionMode: boolean;
        selectedTaskIds: Set<string>;
        onTaskClick: (taskId: string) => void;
        onSetColumnWipLimit: (status: TaskStatus, limit: number | null) => void;
    }) => (
        <div data-testid="kanban-board">
            <span data-testid="lane-mode">{laneMode}</span>
            <span data-testid="selection-mode">{selectionMode ? "on" : "off"}</span>
            {Object.values(tasksByStatus)
                .flat()
                .map((t) => (
                    <div key={t.id}>
                        <button
                            type="button"
                            onClick={() => onTaskClick(t.id)}
                            aria-pressed={selectedTaskIds.has(t.id)}
                        >
                            {t.name}
                        </button>
                        <span>{`${dependencyIndicatorsByTaskId[t.id]?.blockedCount ?? 0}/${dependencyIndicatorsByTaskId[t.id]?.blockingCount ?? 0}`}</span>
                    </div>
                ))}
            <button type="button" onClick={() => onSetColumnWipLimit("BACKLOG", 3)}>
                set backlog limit
            </button>
        </div>
    ),
}));

vi.mock("../components/KanbanToolbar", () => ({
    KanbanToolbar: ({
        selectionMode,
        selectedCount,
        onSelectionModeChange,
        onBulkMoveTargetChange,
        onBulkMove,
    }: {
        selectionMode: boolean;
        selectedCount: number;
        onSelectionModeChange: (enabled: boolean) => void;
        onBulkMoveTargetChange: (status: TaskStatus) => void;
        onBulkMove: () => void;
    }) => (
        <div data-testid="kanban-toolbar">
            <span data-testid="selection-count">{selectedCount}</span>
            <button type="button" onClick={() => onSelectionModeChange(!selectionMode)}>
                {selectionMode ? "disable selection" : "enable selection"}
            </button>
            <button type="button" onClick={() => onBulkMoveTargetChange("DONE")}>
                target done
            </button>
            <button type="button" onClick={onBulkMove}>
                bulk move
            </button>
        </div>
    ),
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

function mockBulkUpdate(overrides?: {
    mutateAsync?: ReturnType<typeof vi.fn>;
    isPending?: boolean;
}) {
    vi.mocked(useBulkUpdateTasks).mockReturnValue({
        mutateAsync: overrides?.mutateAsync ?? vi.fn().mockResolvedValue({ succeeded: 0, failed: 0, errors: [] }),
        isPending: overrides?.isPending ?? false,
    } as never);
}

function mockDependencies(items: Array<{
    id: string;
    predecessor_id: string;
    successor_id: string;
    type: "FS" | "FF" | "SS" | "SF";
    lag: number;
    lag_format: "DURATION" | "PERCENT";
    is_disabled: boolean;
    created_at: string;
}>) {
    vi.mocked(useDependencies).mockReturnValue({
        data: {
            items,
            total: items.length,
            page: 1,
            per_page: 10000,
            total_pages: 1,
        },
    } as never);
}

describe("KanbanPage", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(useProject).mockReturnValue({
            data: {
                id: "proj-1",
                organization_id: "org-1",
                name: "Project",
                start_date: "2025-01-01",
                schedule_from: "start",
                status: "active",
                settings: {
                    auto_calculate: true,
                    hours_per_day: 8,
                    days_per_month: 20,
                    kanban_wip_limits: { BACKLOG: 2 },
                },
                created_at: "2025-01-01T00:00:00Z",
                updated_at: "2025-01-01T00:00:00Z",
            },
        } as never);
        vi.mocked(useUpdateProject).mockReturnValue({
            mutateAsync: vi.fn().mockResolvedValue(undefined),
        } as never);
        mockDependencies([]);
        mockBulkUpdate();
        useKanbanStore.setState({
            collapsedByProject: {},
            laneModeByProject: {},
            searchQuery: "",
            priorityFilter: "all",
            selectedTaskId: null,
            wipLimitsByProject: {},
        });
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
        expect(screen.getByTestId("lane-mode")).toHaveTextContent("none");
        expect(screen.getByText("Deploy API")).toBeInTheDocument();
        expect(screen.getByText("Write docs")).toBeInTheDocument();
        expect(screen.getByText("Authentication")).toBeInTheDocument();
    });

    it("passes project lane mode preference to board", () => {
        mockLoaded(leafTasks);
        useKanbanStore.getState().setProjectLaneMode("proj-1", "assignee");
        render(<KanbanPage />);
        expect(screen.getByTestId("lane-mode")).toHaveTextContent("assignee");
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

    it("opens task detail panel when a card is clicked", async () => {
        const user = userEvent.setup();
        mockLoaded(leafTasks);
        render(<KanbanPage />);

        await user.click(screen.getByRole("button", { name: "Deploy API" }));
        expect(screen.getByTestId("task-detail-panel")).toBeInTheDocument();
        expect(useKanbanStore.getState().selectedTaskId).toBe("t1");
    });

    it("keeps board mounted and interactive while detail panel is open", async () => {
        const user = userEvent.setup();
        mockLoaded(leafTasks);
        render(<KanbanPage />);

        await user.click(screen.getByRole("button", { name: "Deploy API" }));
        expect(screen.getByTestId("task-detail-panel")).toBeInTheDocument();
        expect(screen.getByTestId("kanban-board")).toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Write docs" }));
        expect(useKanbanStore.getState().selectedTaskId).toBe("t2");
    });

    it("updates WIP limit through project settings mutation", async () => {
        const user = userEvent.setup();
        const mutateAsync = vi.fn().mockResolvedValue(undefined);
        vi.mocked(useUpdateProject).mockReturnValue({ mutateAsync } as never);
        mockLoaded(leafTasks);
        render(<KanbanPage />);

        await user.click(screen.getByRole("button", { name: "set backlog limit" }));
        expect(mutateAsync).toHaveBeenCalled();
    });

    it("supports selection mode and bulk move via bulk update API", async () => {
        const user = userEvent.setup();
        const mutateAsync = vi.fn().mockResolvedValue({ succeeded: 2, failed: 0, errors: [] });
        mockBulkUpdate({ mutateAsync });
        mockLoaded(leafTasks);
        render(<KanbanPage />);

        await user.click(screen.getByRole("button", { name: "enable selection" }));
        expect(screen.getByTestId("selection-mode")).toHaveTextContent("on");

        await user.click(screen.getByRole("button", { name: "Deploy API" }));
        await user.click(screen.getByRole("button", { name: "Write docs" }));
        expect(screen.getByTestId("selection-count")).toHaveTextContent("2");

        await user.click(screen.getByRole("button", { name: "target done" }));
        await user.click(screen.getByRole("button", { name: "bulk move" }));

        expect(mutateAsync).toHaveBeenCalledWith({
            tasks: [
                { id: "t1", data: { status: "DONE" } },
                { id: "t2", data: { status: "DONE" } },
            ],
        });
        expect(screen.getByTestId("selection-count")).toHaveTextContent("0");
    });

    it("derives blocked and blocking counts from active dependencies", () => {
        mockLoaded(leafTasks);
        mockDependencies([
            {
                id: "dep-1",
                predecessor_id: "t1",
                successor_id: "t2",
                type: "FS",
                lag: 0,
                lag_format: "DURATION",
                is_disabled: false,
                created_at: "2025-01-01T00:00:00Z",
            },
        ]);

        render(<KanbanPage />);

        expect(screen.getByText("0/1")).toBeInTheDocument();
        expect(screen.getByText("1/0")).toBeInTheDocument();
    });
});
