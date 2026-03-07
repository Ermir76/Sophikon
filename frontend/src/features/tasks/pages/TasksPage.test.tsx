import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TasksPage from "@/features/tasks/pages/TasksPage";
import type { Task } from "@/features/tasks/types";

let capturedBulkEditProps: {
  selectedTaskIds: string[];
  selectedTasks: Task[];
} | null = null;

vi.mock("@/features/tasks/hooks/useTasks", () => ({
  useTasks: vi.fn(),
  useIndentTask: vi.fn(),
  useOutdentTask: vi.fn(),
  useReorderTask: vi.fn(),
  useDeleteTask: vi.fn(),
  useBulkDeleteTasks: vi.fn(),
}));

vi.mock("@/features/tasks/components/task-table/TaskTable", () => ({
  TaskTable: ({
    data,
    setRowSelection,
  }: {
    data: Array<{ id: string }>;
    setRowSelection: (value: Record<string, boolean>) => void;
  }) => (
    <button
      type="button"
      onClick={() =>
        setRowSelection({
          [data[0].id]: true,
          [data[1].id]: true,
        })
      }
    >
      Select Rows
    </button>
  ),
}));

vi.mock("@/features/tasks/components/BulkEditDialog", () => ({
  BulkEditDialog: (props: {
    selectedTaskIds: string[];
    selectedTasks: Task[];
  }) => {
    capturedBulkEditProps = props;
    return <div data-testid="bulk-edit-dialog">Bulk edit open</div>;
  },
}));

vi.mock("@/features/tasks/components/task-detail/TaskDetailPanel", () => ({
  TaskDetailPanel: () => null,
}));

vi.mock("@/features/tasks/components/task-detail/AddDependencyDialog", () => ({
  AddDependencyDialog: () => null,
}));

vi.mock("@/shared/components/QueryError", () => ({
  QueryError: ({ message }: { message: string }) => <div>{message}</div>,
}));

vi.mock("@/shared/components/layout/PageShell", () => ({
  PageShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/shared/components/layout/PageHeader", () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock("@/shared/components/state/PageLoading", () => ({
  PageLoading: () => <div>Loading...</div>,
}));

vi.mock("@/shared/components/state/PageEmpty", () => ({
  PageEmpty: ({
    title,
    action,
  }: {
    title: string;
    action: React.ReactNode;
  }) => (
    <div>
      <div>{title}</div>
      {action}
    </div>
  ),
}));

import {
  useBulkDeleteTasks,
  useDeleteTask,
  useIndentTask,
  useOutdentTask,
  useReorderTask,
  useTasks,
} from "@/features/tasks/hooks/useTasks";

function makeTask(id: string, isSummary: boolean): Task {
  return {
    id,
    project_id: "project-1",
    name: `Task ${id}`,
    notes: "",
    start_date: "2024-01-01",
    finish_date: "2024-01-02",
    duration: 480,
    actual_duration: 0,
    remaining_duration: 480,
    work: 480,
    percent_complete: 0,
    percent_work_complete: 0,
    parent_task_id: undefined,
    wbs_code: "1",
    outline_level: 1,
    order_index: 1,
    sort_order: 1,
    is_summary: isSummary,
    is_milestone: false,
    is_critical: false,
    effort_driven: true,
    priority: 500,
    constraint_type: "ASAP",
    constraint_date: undefined,
    deadline: undefined,
    task_type: "FIXED_UNITS",
    actual_start: undefined,
    actual_finish: undefined,
    actual_cost: 0,
    total_cost: 0,
    fixed_cost: 0,
    total_slack: 0,
    free_slack: 0,
    color: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/projects/project-1/tasks"]}>
      <Routes>
        <Route path="/projects/:projectId/tasks" element={<TasksPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("TasksPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedBulkEditProps = null;

    vi.mocked(useIndentTask).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useOutdentTask).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useReorderTask).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useDeleteTask).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useBulkDeleteTasks).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
  });

  it("passes selected ids and selected tasks to BulkEditDialog", async () => {
    const user = userEvent.setup();
    vi.mocked(useTasks).mockReturnValue({
      data: {
        items: [makeTask("leaf-1", false), makeTask("summary-1", true)],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    renderPage();

    await user.click(screen.getByRole("button", { name: "Select Rows" }));
    expect(screen.getByText("2 selected")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Edit/i }));
    expect(screen.getByTestId("bulk-edit-dialog")).toBeInTheDocument();

    expect(capturedBulkEditProps).not.toBeNull();
    expect(capturedBulkEditProps?.selectedTaskIds).toEqual(["leaf-1", "summary-1"]);
    expect(capturedBulkEditProps?.selectedTasks.map((task) => task.id)).toEqual([
      "leaf-1",
      "summary-1",
    ]);
    expect(
      capturedBulkEditProps?.selectedTasks.filter((task) => task.is_summary).length,
    ).toBe(1);
  });

  it("renders the error state when task loading fails", () => {
    vi.mocked(useTasks).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    } as never);

    renderPage();

    expect(screen.getByText("Failed to load project tasks.")).toBeInTheDocument();
  });
});
