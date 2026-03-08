import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectActivityFeedCard } from "@/features/projects/components/ProjectActivityFeedCard";

vi.mock("date-fns", () => ({
  formatDistanceToNow: vi.fn(() => "2 hours ago"),
}));

describe("ProjectActivityFeedCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the loading state", () => {
    render(<ProjectActivityFeedCard items={[]} isLoading />);

    expect(screen.getByText("Loading project activity...")).toBeInTheDocument();
  });

  it("renders the error state", () => {
    render(
      <ProjectActivityFeedCard
        items={[]}
        isError
        error={new Error("Activity unavailable")}
      />,
    );

    expect(screen.getByText("Activity unavailable")).toBeInTheDocument();
  });

  it("renders the empty state", () => {
    render(<ProjectActivityFeedCard items={[]} />);

    expect(screen.getByText("No recent activity for this project.")).toBeInTheDocument();
  });

  it("renders activity items with actor, entity label, timestamp, and change summary", () => {
    render(
      <ProjectActivityFeedCard
        items={[
          {
            id: "activity-1",
            entity_type: "task",
            entity_name: "Release prep",
            action: "updated",
            created_at: "2026-03-07T12:00:00Z",
            user: { id: "user-1", full_name: "Jane Doe", avatar_url: null },
            changes: {
              fields: [
                { field: "percent_complete", old: 10, new: 25 },
                { field: "finish_date", old: "2026-03-09", new: "2026-03-10" },
              ],
            },
          },
        ]}
      />,
    );

    expect(screen.getByText("Recent Project Activity")).toBeInTheDocument();
    expect(screen.getByText("Task")).toBeInTheDocument();
    expect(screen.getByText("Release prep")).toBeInTheDocument();
    expect(screen.getByText("2 hours ago")).toBeInTheDocument();
    expect(screen.getByText("Jane Doe updated this task.")).toBeInTheDocument();
    expect(
      screen.getByText("Changed percent complete and finish date."),
    ).toBeInTheDocument();
  });
});
