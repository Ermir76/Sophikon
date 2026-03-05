import { useQuery } from "@tanstack/react-query";
import { projectOverviewInsightsService } from "@/features/projects/api/project-overview-insights.service";
import type { TimeWindowSelection } from "@/shared/types/insights";

export const projectOverviewInsightsKeys = {
  all: ["insights", "project-overview"] as const,
  detail: (projectId: string | null | undefined, window: TimeWindowSelection) =>
    [
      ...projectOverviewInsightsKeys.all,
      projectId,
      window.windowPreset,
      window.startDate ?? "",
      window.endDate ?? "",
    ] as const,
};

function isWindowValid(window: TimeWindowSelection) {
  if (window.windowPreset !== "custom") return true;
  return !!window.startDate && !!window.endDate;
}

export function useProjectOverviewInsights(
  projectId: string | null | undefined,
  window: TimeWindowSelection,
) {
  return useQuery({
    queryKey: projectOverviewInsightsKeys.detail(projectId, window),
    queryFn: () => projectOverviewInsightsService.getByProject(projectId!, window),
    enabled: !!projectId && isWindowValid(window),
  });
}
