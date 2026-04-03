import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { InsightsActivityCard } from "@/shared/ui/insights-activity-card";

vi.mock("date-fns", async (importOriginal) => {
  const actual = await importOriginal<typeof import("date-fns")>();
  return {
    ...actual,
    formatDistanceToNow: vi.fn(() => "recently"),
  };
});

describe("InsightsActivityCard", () => {
  it("routes project, task, and resource activity items to the correct pages", () => {
    render(
      <MemoryRouter>
        <InsightsActivityCard
          title="Recent Activity"
          emptyMessage="No recent activity."
          items={[
            {
              entity_type: "project",
              entity_id: "project-1",
              entity_name: "Project Alpha",
              action: "created",
              timestamp: "2026-04-02T10:00:00Z",
              project_id: "project-1",
              project_name: "Project Alpha",
            },
            {
              entity_type: "task",
              entity_id: "task-1",
              entity_name: "Task Bravo",
              action: "updated",
              timestamp: "2026-04-02T11:00:00Z",
              project_id: "project-1",
              project_name: "Project Alpha",
            },
            {
              entity_type: "resource",
              entity_id: "resource-1",
              entity_name: "Resource Charlie",
              action: "updated",
              timestamp: "2026-04-02T12:00:00Z",
              project_id: "project-1",
              project_name: "Project Alpha",
            },
          ]}
        />
      </MemoryRouter>,
    );

    expect(
      screen.getByText("Project Alpha", { selector: "span" }).closest("a"),
    ).toHaveAttribute("href", "/projects/project-1");
    expect(
      screen.getByText("Task Bravo", { selector: "span" }).closest("a"),
    ).toHaveAttribute("href", "/projects/project-1/tasks");
    expect(
      screen.getByText("Resource Charlie", { selector: "span" }).closest("a"),
    ).toHaveAttribute("href", "/projects/project-1/resources");
  });
});
