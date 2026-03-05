import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { useProjectOverviewInsights } from "@/features/projects/hooks/useProjectOverviewInsights";

vi.mock("@/features/projects/api/project-overview-insights.service", () => ({
  projectOverviewInsightsService: {
    getByProject: vi.fn(),
  },
}));

import { projectOverviewInsightsService } from "@/features/projects/api/project-overview-insights.service";

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useProjectOverviewInsights", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches when project and valid window are present", async () => {
    (projectOverviewInsightsService.getByProject as any).mockResolvedValue({
      kpis: { total_tasks: 1 },
      schedule: { start_date: "2026-01-01", milestones_due_soon: 0 },
      trend: [],
      risk_items: [],
      recent_activity: [],
    });

    const window = { windowPreset: "30d" as const };
    const { result } = renderHook(
      () => useProjectOverviewInsights("project-1", window),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(projectOverviewInsightsService.getByProject).toHaveBeenCalledWith("project-1", window);
  });

  it("does not fetch custom window without both dates", () => {
    const window = { windowPreset: "custom" as const, endDate: "2026-03-10" };
    const { result } = renderHook(
      () => useProjectOverviewInsights("project-1", window),
      { wrapper: createWrapper() },
    );

    expect(result.current.fetchStatus).toBe("idle");
    expect(projectOverviewInsightsService.getByProject).not.toHaveBeenCalled();
  });
});
