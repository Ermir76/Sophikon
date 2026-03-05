import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { useDashboardInsights } from "@/features/dashboard/hooks/useDashboardInsights";

vi.mock("@/features/dashboard/api/dashboard-insights.service", () => ({
  dashboardInsightsService: {
    getByOrganization: vi.fn(),
  },
}));

import { dashboardInsightsService } from "@/features/dashboard/api/dashboard-insights.service";

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useDashboardInsights", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches when organization and valid window are present", async () => {
    (dashboardInsightsService.getByOrganization as any).mockResolvedValue({
      kpis: { active_projects: 1 },
      project_health: [],
      trend: [],
      recent_activity: [],
    });

    const window = { windowPreset: "30d" as const };
    const { result } = renderHook(
      () => useDashboardInsights("org-1", window),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(dashboardInsightsService.getByOrganization).toHaveBeenCalledWith("org-1", window);
  });

  it("does not fetch custom window without both dates", () => {
    const window = { windowPreset: "custom" as const, startDate: "2026-03-01" };
    const { result } = renderHook(
      () => useDashboardInsights("org-1", window),
      { wrapper: createWrapper() },
    );

    expect(result.current.fetchStatus).toBe("idle");
    expect(dashboardInsightsService.getByOrganization).not.toHaveBeenCalled();
  });
});
