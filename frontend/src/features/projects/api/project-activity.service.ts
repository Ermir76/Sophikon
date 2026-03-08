import { api } from "@/shared/api/api";
import type { PaginatedResponse } from "@/shared/types/api";
import type { ProjectActivityAction, ProjectActivityEntityType, ProjectActivityItem } from "@/features/projects/types";

export interface ProjectActivityFilters {
  page?: number;
  per_page?: number;
  user_id?: string;
  entity_type?: ProjectActivityEntityType;
  action?: ProjectActivityAction;
}

export const projectActivityService = {
  async list(
    projectId: string,
    filters: ProjectActivityFilters = {},
  ): Promise<PaginatedResponse<ProjectActivityItem>> {
    const response = await api.get<PaginatedResponse<ProjectActivityItem>>(
      `/projects/${projectId}/activity`,
      { params: filters },
    );
    return response.data;
  },
};
