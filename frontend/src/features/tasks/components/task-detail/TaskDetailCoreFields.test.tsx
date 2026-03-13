import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TaskDetailCoreFields } from "@/features/tasks/components/task-detail/TaskDetailCoreFields";
import type { Task, TaskUpdate } from "@/features/tasks/types";

vi.mock("@/shared/components/ColorPicker", () => ({
  ColorPicker: () => <div>Color picker</div>,
}));

const baseTask: Task = {
  id: "task-1",
  project_id: "project-1",
  name: "Parent task",
  notes: "Notes",
  start_date: "2024-01-01",
  finish_date: "2024-01-05",
  duration: 2400,
  work: 960,
  percent_complete: 50,
  percent_work_complete: 50,
  parent_task_id: undefined,
  wbs_code: "1",
  outline_level: 1,
  order_index: 1,
  sort_order: 1,
  is_summary: true,
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
  color: "#ff0000",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-02T00:00:00Z",
};

function renderFields(task: Task, overrides?: Partial<Parameters<typeof TaskDetailCoreFields>[0]>) {
  const localData: Partial<TaskUpdate> = {
    percent_complete: task.percent_complete,
    start_date: task.start_date,
    duration: task.duration,
    notes: task.notes,
    calendar_id: task.calendar_id ?? null,
  };

  return render(
    <TaskDetailCoreFields
      task={task}
      localData={localData}
      setLocalData={vi.fn()}
      handleBlur={vi.fn()}
      calendarOptions={[{ id: "cal-1", name: "Team Calendar" }]}
      onColorChange={vi.fn()}
      {...overrides}
    />,
  );
}

describe("TaskDetailCoreFields", () => {
  it("renders summary task rollup fields as read-only", () => {
    renderFields(baseTask);

    expect(
      screen.getByText("Schedule and progress for summary tasks are computed from subtasks."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("% Complete")).toBeDisabled();
    expect(screen.getByLabelText("Start Date")).toBeDisabled();
    expect(screen.getByRole("spinbutton", { name: /Duration/i })).toBeDisabled();
  });

  it("keeps non-summary task fields editable", () => {
    renderFields({ ...baseTask, is_summary: false, color: null });

    expect(
      screen.queryByText("Schedule and progress for summary tasks are computed from subtasks."),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText("% Complete")).not.toBeDisabled();
    expect(screen.getByLabelText("Start Date")).not.toBeDisabled();
    expect(screen.getByRole("spinbutton", { name: /Duration/i })).not.toBeDisabled();
  });

  it("renders a labeled calendar selector", () => {
    renderFields({ ...baseTask, is_summary: false, color: null });

    expect(screen.getByRole("combobox", { name: /Calendar/i })).toBeInTheDocument();
  });
});
