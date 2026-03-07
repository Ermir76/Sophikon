import { useQuery } from "@tanstack/react-query";

import { projectService } from "@/features/projects/api/project.service";
import type { TimeWindowSelection } from "@/shared/types/insights";

const DEFAULT_WINDOW: TimeWindowSelection = { windowPreset: "30d" };

function normalizeWindow(window?: TimeWindowSelection): TimeWindowSelection {
  return window ?? DEFAULT_WINDOW;
}

function isWindowValid(window: TimeWindowSelection) {
  if (window.windowPreset !== "custom") return true;
  return Boolean(window.startDate && window.endDate);
}

export const projectDashboardKeys = {
  all: ["projects", "dashboard"] as const,
  detail: (projectId: string | null | undefined, window?: TimeWindowSelection) => {
    const selection = normalizeWindow(window);

    return [
      ...projectDashboardKeys.all,
      projectId,
      selection.windowPreset,
      selection.startDate ?? "",
      selection.endDate ?? "",
    ] as const;
  },
};

export function useProjectDashboard(
  projectId: string | null | undefined,
  window?: TimeWindowSelection,
) {
  const selection = normalizeWindow(window);

  return useQuery({
    queryKey: projectDashboardKeys.detail(projectId, selection),
    queryFn: () => projectService.getDashboard(projectId!, selection),
    enabled: Boolean(projectId) && isWindowValid(selection),
  });
}
