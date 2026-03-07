import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProjectOverviewPage from "@/features/projects/pages/ProjectOverviewPage";

vi.mock("@/features/projects/hooks/useProjects", () => ({
  useProject: vi.fn(),
}));

vi.mock("@/features/projects/hooks/useProjectDashboard", () => ({
  useProjectDashboard: vi.fn(),
}));

vi.mock("@/features/ai/hooks/useAi", () => ({
  useAiSuggestions: vi.fn(),
}));

import { useAiSuggestions } from "@/features/ai/hooks/useAi";
import { useProjectDashboard } from "@/features/projects/hooks/useProjectDashboard";
import { useProject } from "@/features/projects/hooks/useProjects";

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/projects/project-1"]}>
      <Routes>
        <Route path="/projects/:projectId" element={<ProjectOverviewPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProjectOverviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useProject).mockReturnValue({
      data: { id: "project-1", name: "Launch Program" },
      isLoading: false,
      isError: false,
      error: null,
    } as never);

    vi.mocked(useProjectDashboard).mockReturnValue({
      data: {
        summary: {
          total_tasks: 4,
          completed_tasks: 1,
          in_progress_tasks: 1,
          not_started_tasks: 2,
          overdue_tasks: 1,
          milestones: 1,
          milestones_completed: 0,
          percent_complete: 25,
        },
        schedule: {
          start_date: "2026-03-01",
          finish_date: "2026-03-12",
          duration_days: 11,
          days_elapsed: 6,
          days_remaining: 5,
        },
        resources: { total_resources: 1, overallocated_count: 1 },
        cost: { budget: 15000, total_cost: 6600, actual_cost: 3600, remaining_cost: 3000 },
        critical_path: { task_count: 1, total_duration_days: 2, path_length_days: 2 },
        upcoming_milestones: [
          {
            task_id: "task-1",
            name: "Upcoming milestone",
            finish_date: "2026-03-12",
            percent_complete: 0,
          },
        ],
        overdue_tasks: [
          {
            task_id: "task-2",
            name: "Overdue critical task",
            finish_date: "2026-03-05",
            percent_complete: 25,
            days_overdue: 2,
          },
        ],
        recent_activity: [
          {
            entity_type: "task",
            entity_id: "task-2",
            entity_name: "Overdue critical task",
            action: "updated",
            timestamp: "2026-03-07T12:00:00Z",
            project_id: "project-1",
            project_name: "Launch Program",
          },
        ],
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as never);
  });

  it("renders the dashboard sections and project drill-down links", () => {
    vi.mocked(useAiSuggestions).mockReturnValue({
      data: {
        suggestions: [
          {
            id: "s-1",
            type: "risk",
            severity: "HIGH",
            title: "Critical path drag",
            description: "One overdue critical task is compressing float.",
          },
        ],
      },
      isLoading: false,
      isError: false,
    } as never);

    renderPage();

    expect(useProjectDashboard).toHaveBeenCalledWith("project-1", {
      windowPreset: "30d",
      startDate: undefined,
      endDate: undefined,
    });

    expect(screen.getByText("Tasks by Status")).toBeInTheDocument();
    expect(screen.getByText("Upcoming Milestones")).toBeInTheDocument();
    expect(screen.getByText("Overdue Tasks")).toBeInTheDocument();
    expect(screen.getByText("Critical Path Summary")).toBeInTheDocument();
    expect(screen.getByText("Resource Utilization")).toBeInTheDocument();
    expect(screen.getByText("Cost Summary")).toBeInTheDocument();
    expect(screen.getByText("AI Risk Signals")).toBeInTheDocument();
    expect(screen.getByText("Critical path drag")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Upcoming milestone/i })).toHaveAttribute(
      "href",
      "/projects/project-1/tasks",
    );
    expect(screen.getByRole("link", { name: /Overdue critical task/i })).toHaveAttribute(
      "href",
      "/projects/project-1/tasks",
    );
    expect(screen.getByRole("link", { name: /Resources/i })).toHaveAttribute(
      "href",
      "/projects/project-1/resources",
    );
  });

  it("keeps the dashboard visible when AI suggestions fail", () => {
    vi.mocked(useAiSuggestions).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as never);

    renderPage();

    expect(screen.getByText("Tasks by Status")).toBeInTheDocument();
    expect(screen.getByText("Upcoming milestone")).toBeInTheDocument();
    expect(screen.getByText("AI insights are unavailable right now.")).toBeInTheDocument();
  });

  it("shows the window validation message for an incomplete custom range", () => {
    vi.mocked(useAiSuggestions).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as never);

    render(
      <MemoryRouter initialEntries={["/projects/project-1?ov_window=custom&ov_start=2026-03-01"]}>
        <Routes>
          <Route path="/projects/:projectId" element={<ProjectOverviewPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText("For a custom window, please select both start and end date."),
    ).toBeInTheDocument();
  });
});
