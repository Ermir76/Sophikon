import { api } from "@/shared/api/api";
import type { Project, ProjectCreate, ProjectUpdate } from "@/features/projects/types";

export const projectService = {
  list: async (orgId: string) => {
    const response = await api.get<{ items: Project[]; total: number }>(
      "/projects",
      { params: { organization_id: orgId } },
    );
    return response.data;
  },

  get: async (projectId: string) => {
    const response = await api.get<Project>(`/projects/${projectId}`);
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
