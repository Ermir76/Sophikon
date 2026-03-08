import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { taskColumns } from "@/features/tasks/components/task-table/TaskTableColumns";
import type { Task } from "@/features/tasks/types";

function makeTask(commentsCount?: number): Task {
    return {
        id: "task-1",
        project_id: "project-1",
        name: "Task One",
        notes: "",
        start_date: "2026-03-08",
        finish_date: "2026-03-09",
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
        is_summary: false,
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
        comments_count: commentsCount,
        created_at: "2026-03-08T00:00:00Z",
        updated_at: "2026-03-08T00:00:00Z",
    };
}

function renderCommentsCell(task: Task) {
    const commentsColumn = taskColumns.find((column) => (column as { id?: string }).id === "comments");
    expect(commentsColumn).toBeDefined();
    const cell = (commentsColumn as { cell: (info: unknown) => ReactNode }).cell;
    return render(
        <>{cell({ row: { original: task } })}</>,
    );
}

describe("TaskTableColumns comments column", () => {
    it("renders explicit comment count", () => {
        renderCommentsCell(makeTask(7));
        expect(screen.getByText("7")).toBeInTheDocument();
    });

    it("falls back to zero when count is missing", () => {
        renderCommentsCell(makeTask(undefined));
        expect(screen.getByText("0")).toBeInTheDocument();
    });
});
