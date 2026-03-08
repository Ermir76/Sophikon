import { useQuery } from "@tanstack/react-query";

import {
  projectActivityService,
  type ProjectActivityFilters,
} from "@/features/projects/api/project-activity.service";

interface NormalizedProjectActivityFilters {
  page: number;
  per_page: number;
  user_id: string;
  entity_type: string;
  action: string;
}

function normalizeFilters(
  filters?: ProjectActivityFilters | NormalizedProjectActivityFilters,
): NormalizedProjectActivityFilters {
  return {
    page: filters?.page ?? 1,
    per_page: filters?.per_page ?? 20,
    user_id: filters?.user_id ?? "",
    entity_type: filters?.entity_type ?? "",
    action: filters?.action ?? "",
  };
}

export const projectActivityKeys = {
  all: ["project-activity"] as const,
  list: (
    projectId: string | null | undefined,
    filters?: ProjectActivityFilters | NormalizedProjectActivityFilters,
  ) => {
    const normalized = normalizeFilters(filters);
    return [
      ...projectActivityKeys.all,
      projectId,
      normalized.page,
      normalized.per_page,
      normalized.user_id,
      normalized.entity_type,
      normalized.action,
    ] as const;
  },
};

export function useProjectActivity(
  projectId: string | null | undefined,
  filters?: ProjectActivityFilters,
) {
  const normalized = normalizeFilters(filters);

  return useQuery({
    queryKey: projectActivityKeys.list(projectId, normalized),
    queryFn: () =>
      projectActivityService.list(projectId!, {
        page: normalized.page,
        per_page: normalized.per_page,
        user_id: normalized.user_id || undefined,
        entity_type: (normalized.entity_type || undefined) as ProjectActivityFilters["entity_type"],
        action: (normalized.action || undefined) as ProjectActivityFilters["action"],
      }),
    enabled: Boolean(projectId),
  });
}
