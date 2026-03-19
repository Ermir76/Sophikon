import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { KanbanCard } from "./KanbanCard";
import type { Task } from "@/features/tasks";

vi.mock("@dnd-kit/core", () => ({
    useDraggable: () => ({
        setNodeRef: vi.fn(),
        listeners: {},
        attributes: {},
        isDragging: false,
    }),
}));

const baseTask: Task = {
    id: "task-1",
    project_id: "project-1",
    name: "Build Auth System",
    start_date: "2025-01-01",
    finish_date: "2030-12-31",
    duration: 2400,
    work: 960,
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
};

describe("KanbanCard", () => {
    it("renders task name and WBS code", () => {
        render(<KanbanCard task={baseTask} />);
        expect(screen.getByText("Build Auth System")).toBeInTheDocument();
        expect(screen.getByText("1.1")).toBeInTheDocument();
    });

    it("shows HIGH badge for priority >= 750", () => {
        render(<KanbanCard task={{ ...baseTask, priority: 800 }} />);
        expect(screen.getByText("HIGH")).toBeInTheDocument();
    });

    it("shows MED badge for priority >= 500 and < 750", () => {
        render(<KanbanCard task={{ ...baseTask, priority: 600 }} />);
        expect(screen.getByText("MED")).toBeInTheDocument();
    });

    it("shows LOW badge for priority >= 250 and < 500", () => {
        render(<KanbanCard task={{ ...baseTask, priority: 300 }} />);
        expect(screen.getByText("LOW")).toBeInTheDocument();
    });

    it("shows no priority badge for priority < 250", () => {
        render(<KanbanCard task={{ ...baseTask, priority: 100 }} />);
        expect(screen.queryByText("HIGH")).not.toBeInTheDocument();
        expect(screen.queryByText("MED")).not.toBeInTheDocument();
        expect(screen.queryByText("LOW")).not.toBeInTheDocument();
    });

    it("renders progress bar when percent_complete > 0", () => {
        render(<KanbanCard task={{ ...baseTask, percent_complete: 65 }} />);
        expect(screen.getByText("65%")).toBeInTheDocument();
    });

    it("does not render progress bar when percent_complete is 0", () => {
        render(<KanbanCard task={{ ...baseTask, percent_complete: 0 }} />);
        expect(screen.queryByText("%")).not.toBeInTheDocument();
    });

    it("shows deadline when task has one", () => {
        render(<KanbanCard task={{ ...baseTask, deadline: "2030-06-15" }} />);
        expect(screen.getByText("Jun 15")).toBeInTheDocument();
    });

    it("shows overdue indicator when finish_date is in the past and status is not DONE", () => {
        render(<KanbanCard task={{ ...baseTask, finish_date: "2020-01-01", deadline: "2020-03-15", status: "IN_PROGRESS" }} />);
        // deadline date renders in destructive color when overdue
        const deadlineText = screen.getByText("Mar 15");
        expect(deadlineText).toHaveClass("text-destructive");
    });

    it("does not show overdue indicator when status is DONE", () => {
        render(<KanbanCard task={{ ...baseTask, finish_date: "2020-01-01", status: "DONE" }} />);
        expect(screen.queryByText("Jan 1")).not.toBeInTheDocument();
    });

    it("shows comment count when task has comments", () => {
        render(<KanbanCard task={{ ...baseTask, comments_count: 3 }} />);
        expect(screen.getByText("3")).toBeInTheDocument();
    });

    it("does not apply opacity class when isDragOverlay is true", () => {
        const { container } = render(<KanbanCard task={baseTask} isDragOverlay />);
        expect(container.firstChild).not.toHaveClass("opacity-40");
    });
});
