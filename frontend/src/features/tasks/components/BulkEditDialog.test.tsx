import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BulkEditDialog } from "@/features/tasks/components/BulkEditDialog";
import type { Task } from "@/features/tasks/types";

const mockMutateAsync = vi.fn();
const mockToastError = vi.fn();
const mockToastSuccess = vi.fn();
const mockToastInfo = vi.fn();

vi.mock("@/features/tasks/hooks/useTasks", () => ({
  useBulkUpdateTasks: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: {
    error: (...args: unknown[]) => mockToastError(...args),
    success: (...args: unknown[]) => mockToastSuccess(...args),
    info: (...args: unknown[]) => mockToastInfo(...args),
  },
}));

import { useBulkUpdateTasks } from "@/features/tasks/hooks/useTasks";

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

describe("BulkEditDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useBulkUpdateTasks).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as never);
  });

  it("filters out summary tasks for % complete and reports skipped summaries", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const onSuccess = vi.fn();

    mockMutateAsync.mockResolvedValue({
      succeeded: 1,
      failed: 0,
      errors: [],
    });

    render(
      <BulkEditDialog
        projectId="project-1"
        selectedTaskIds={["leaf-1", "summary-1"]}
        selectedTasks={[makeTask("leaf-1", false), makeTask("summary-1", true)]}
        isOpen={true}
        onClose={onClose}
        onSuccess={onSuccess}
      />,
    );

    const inputs = screen.getAllByPlaceholderText("Leave empty to skip");
    await user.type(inputs[0], "40");
    await user.click(screen.getByRole("button", { name: "Apply Changes" }));

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(mockMutateAsync).toHaveBeenCalledWith({
      tasks: [{ id: "leaf-1", data: { percent_complete: 40 } }],
    });
    expect(mockToastInfo).toHaveBeenCalledWith(
      "1 summary task(s) skipped — their progress is calculated from subtasks",
    );
    expect(mockToastSuccess).toHaveBeenCalledWith("1 task(s) updated");
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("disables submit for summary-only percent edits", async () => {
    const user = userEvent.setup();

    render(
      <BulkEditDialog
        projectId="project-1"
        selectedTaskIds={["summary-1"]}
        selectedTasks={[makeTask("summary-1", true)]}
        isOpen={true}
        onClose={vi.fn()}
      />,
    );

    const inputs = screen.getAllByPlaceholderText("Leave empty to skip");
    await user.type(inputs[0], "50");

    expect(
      screen.getByText(
        "All selected tasks are summaries. Their % Complete is calculated from subtasks.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply Changes" })).toBeDisabled();
    expect(mockMutateAsync).not.toHaveBeenCalled();
  });
});
