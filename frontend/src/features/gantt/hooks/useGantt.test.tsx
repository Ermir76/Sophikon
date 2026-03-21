import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import GanttPage from "@/features/gantt/pages/GanttPage";

type MockTask = {
  id: string;
  project_id: string;
  name: string;
  start_date: string;
  finish_date: string;
  parent_task_id?: string;
  order_index: number;
  sort_order: number;
};

const mocks = vi.hoisted(() => ({
  useTasks: vi.fn(),
  useDependencies: vi.fn(),
  useProject: vi.fn(),
  useUpdateProject: vi.fn(),
  useCollapsedTree: vi.fn(),
  calculateMutateAsync: vi.fn(),
}));

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useParams: () => ({ projectId: "proj-1" }),
  };
});

vi.mock("@/features/tasks", () => ({
  useTasks: mocks.useTasks,
  useDependencies: mocks.useDependencies,
  TaskDetailPanel: () => null,
}));

vi.mock("@/features/projects", () => ({
  useProject: mocks.useProject,
  useUpdateProject: mocks.useUpdateProject,
}));

vi.mock("@/shared/hooks/useCollapsedTree", () => ({
  useCollapsedTree: mocks.useCollapsedTree,
}));

vi.mock("@/features/gantt/hooks/useSchedule", () => ({
  useCalculateSchedule: () => ({
    mutateAsync: mocks.calculateMutateAsync,
    isPending: false,
  }),
}));

vi.mock("@/features/gantt/components/GanttContainer", () => ({
  GanttContainer: () => <div data-testid="gantt-container">Mock Gantt Container</div>,
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

function makeTask(id: string, startDate: string, finishDate: string): MockTask {
  return {
    id,
    project_id: "proj-1",
    name: `Task ${id}`,
    start_date: startDate,
    finish_date: finishDate,
    parent_task_id: undefined,
    order_index: 1,
    sort_order: 1,
  };
}

function setupLoadedState(tasks: MockTask[]) {
  mocks.useTasks.mockReturnValue({
    data: { items: tasks },
    isLoading: false,
    error: null,
  });
  mocks.useDependencies.mockReturnValue({
    data: { items: [] },
    isLoading: false,
    error: null,
  });
  mocks.useProject.mockReturnValue({
    data: { settings: { auto_calculate: true }, color: "#0f6b43" },
  });
  mocks.useUpdateProject.mockReturnValue({
    mutateAsync: vi.fn(),
  });
  mocks.useCollapsedTree.mockImplementation((_key: string, data: MockTask[]) => ({
    visibleData: data,
    collapsedIds: new Set<string>(),
    toggleCollapse: vi.fn(),
  }));
}

describe("useGantt / GanttPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it("renders gantt page without crash", () => {
    setupLoadedState([
      makeTask("1", "2024-01-01", "2024-01-03"),
      makeTask("2", "2024-01-04", "2024-01-05"),
    ]);

    render(<GanttPage />);

    expect(screen.getByRole("heading", { name: "Gantt Chart" })).toBeInTheDocument();
    expect(screen.getByTestId("gantt-container")).toBeInTheDocument();
  });

  it("fetches tasks and dependencies on mount", () => {
    setupLoadedState([makeTask("1", "2024-01-01", "2024-01-03")]);

    render(<GanttPage />);

    expect(mocks.useTasks).toHaveBeenCalledWith("proj-1");
    expect(mocks.useDependencies).toHaveBeenCalledWith("proj-1");
  });

  it("timeline zoom switches between day week month", async () => {
    const user = userEvent.setup();
    setupLoadedState([makeTask("1", "2024-01-01", "2024-01-03")]);

    render(<GanttPage />);

    expect(screen.getByText("week")).toBeInTheDocument();

    await user.click(screen.getByTitle("Zoom in"));
    expect(screen.getByText("day")).toBeInTheDocument();

    await user.click(screen.getByTitle("Zoom out"));
    expect(screen.getByText("week")).toBeInTheDocument();

    await user.click(screen.getByTitle("Zoom out"));
    expect(screen.getByText("month")).toBeInTheDocument();
  });

  it("displays loading state while fetching", () => {
    mocks.useTasks.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    mocks.useDependencies.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
    mocks.useProject.mockReturnValue({ data: undefined });
    mocks.useUpdateProject.mockReturnValue({ mutateAsync: vi.fn() });
    mocks.useCollapsedTree.mockReturnValue({
      visibleData: [],
      collapsedIds: new Set<string>(),
      toggleCollapse: vi.fn(),
    });

    render(<GanttPage />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("displays error state on fetch failure", () => {
    mocks.useTasks.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("task fetch failed"),
    });
    mocks.useDependencies.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
    mocks.useProject.mockReturnValue({ data: undefined });
    mocks.useUpdateProject.mockReturnValue({ mutateAsync: vi.fn() });
    mocks.useCollapsedTree.mockReturnValue({
      visibleData: [],
      collapsedIds: new Set<string>(),
      toggleCollapse: vi.fn(),
    });

    render(<GanttPage />);

    expect(screen.getByText("Failed to load Gantt chart data.")).toBeInTheDocument();
  });

  it("displays empty state when no tasks", () => {
    setupLoadedState([]);

    render(<GanttPage />);

    expect(screen.getByText("No tasks to display")).toBeInTheDocument();
    expect(
      screen.getByText("Add tasks to your project to see them on the Gantt chart."),
    ).toBeInTheDocument();
  });
});
