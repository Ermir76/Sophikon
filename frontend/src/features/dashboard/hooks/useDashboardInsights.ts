import { useQuery } from "@tanstack/react-query";
import { dashboardInsightsService } from "@/features/dashboard/api/dashboard-insights.service";
import type { TimeWindowSelection } from "@/shared/types/insights";

export const dashboardInsightsKeys = {
  all: ["insights", "dashboard"] as const,
  detail: (organizationId: string | null | undefined, window: TimeWindowSelection) =>
    [
      ...dashboardInsightsKeys.all,
      organizationId,
      window.windowPreset,
      window.startDate ?? "",
      window.endDate ?? "",
    ] as const,
};

function isWindowValid(window: TimeWindowSelection) {
  if (window.windowPreset !== "custom") return true;
  return !!window.startDate && !!window.endDate;
}

export function useDashboardInsights(
  organizationId: string | null | undefined,
  window: TimeWindowSelection,
) {
  return useQuery({
    queryKey: dashboardInsightsKeys.detail(organizationId, window),
    queryFn: () => dashboardInsightsService.getByOrganization(organizationId!, window),
    enabled: !!organizationId && isWindowValid(window),
  });
}
