import { api } from "@/shared/api/api";
import { buildInsightsWindowParams } from "@/shared/api/insights-params";
import type { TimeWindowSelection } from "@/shared/types/insights";
import type {
  Project,
  ProjectCreate,
  ProjectDashboard,
  ProjectUpdate,
} from "@/features/projects/types";
import type { PaginatedResponse } from "@/shared/types/api";

export const projectService = {
  list: async (orgId: string) => {
    const response = await api.get<PaginatedResponse<Project>>(
      "/projects",
      { params: { organization_id: orgId } },
    );
    return response.data;
  },

  get: async (projectId: string) => {
    const response = await api.get<Project>(`/projects/${projectId}`);
    return response.data;
  },

  getDashboard: async (
    projectId: string,
    window: TimeWindowSelection = { windowPreset: "30d" },
  ) => {
    const response = await api.get<ProjectDashboard>(`/projects/${projectId}/dashboard`, {
      params: buildInsightsWindowParams(window),
    });
    return response.data;
  },

  create: async (
    orgId: string,
    data: Omit<ProjectCreate, "organization_id">,
  ) => {
    const response = await api.post<Project>(`/projects`, {
      ...data,
      organization_id: orgId,
    });
    return response.data;
  },

  update: async (projectId: string, data: ProjectUpdate) => {
    const response = await api.patch<Project>(`/projects/${projectId}`, data);
    return response.data;
  },

  delete: async (projectId: string) => {
    await api.delete(`/projects/${projectId}`);
  },
};
