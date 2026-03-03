import { api } from "@/shared/api/api";
import type { Resource, ResourceCreate, ResourceUpdate } from "@/features/resources/types";
import type { PaginatedResponse } from "@/shared/types/api";

export const resourceService = {
    list: async (projectId: string) => {
        const response = await api.get<PaginatedResponse<Resource>>(`/projects/${projectId}/resources?include_inactive=true`);
        return response.data;
    },

    get: async (projectId: string, resourceId: string) => {
        const response = await api.get<Resource>(`/projects/${projectId}/resources/${resourceId}`);
        return response.data;
    },

    create: async (projectId: string, data: ResourceCreate) => {
        const response = await api.post<Resource>(`/projects/${projectId}/resources`, data);
        return response.data;
    },

    update: async (projectId: string, resourceId: string, data: ResourceUpdate) => {
        const response = await api.patch<Resource>(`/projects/${projectId}/resources/${resourceId}`, data);
        return response.data;
    },

    delete: async (projectId: string, resourceId: string) => {
        await api.delete(`/projects/${projectId}/resources/${resourceId}`);
    },
};
