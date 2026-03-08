import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";

import { useProjectDashboard } from "@/features/projects/hooks/useProjectDashboard";

vi.mock("@/features/projects/api/project.service", () => ({
  projectService: {
    getDashboard: vi.fn(),
  },
}));

import { projectService } from "@/features/projects/api/project.service";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useProjectDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches dashboard data with the default window", async () => {
    vi.mocked(projectService.getDashboard).mockResolvedValue({
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
      upcoming_milestones: [],
      overdue_tasks: [],
    });

    const { result } = renderHook(() => useProjectDashboard("project-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(projectService.getDashboard).toHaveBeenCalledWith("project-1", {
      windowPreset: "30d",
    });
  });

  it("does not fetch an invalid custom window", () => {
    const { result } = renderHook(
      () =>
        useProjectDashboard("project-1", {
          windowPreset: "custom",
          startDate: "2026-03-01",
        }),
      { wrapper: createWrapper() },
    );

    expect(result.current.fetchStatus).toBe("idle");
    expect(projectService.getDashboard).not.toHaveBeenCalled();
  });
});
