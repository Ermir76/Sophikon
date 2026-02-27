import { api } from "@/shared/api/api";
import type { Dependency, DependencyCreate, DependencyUpdate } from "@/features/tasks/types";

export const dependencyService = {
    list: async (projectId: string) => {
        const response = await api.get<{ items: Dependency[]; total: number }>(`/projects/${projectId}/dependencies`);
        return response.data;
    },

    create: async (projectId: string, data: DependencyCreate) => {
        const response = await api.post<Dependency>(`/projects/${projectId}/dependencies`, data);
        return response.data;
    },

    update: async (projectId: string, dependencyId: string, data: DependencyUpdate) => {
        const response = await api.patch<Dependency>(`/projects/${projectId}/dependencies/${dependencyId}`, data);
        return response.data;
    },

    delete: async (projectId: string, dependencyId: string) => {
        await api.delete(`/projects/${projectId}/dependencies/${dependencyId}`);
    }
};
