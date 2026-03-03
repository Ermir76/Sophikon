import { api } from "@/shared/api/api";
import type {
    Task,
    TaskCreate,
    TaskUpdate,
    TaskReorder,
    TaskBulkCreate,
    TaskBulkUpdate,
    TaskBulkDelete,
    TaskBulkCreateResponse,
    BulkOperationResponse
} from "@/features/tasks/types";
import type { PaginatedResponse } from "@/shared/types/api";

export const taskService = {
    list: async (projectId: string) => {
        const response = await api.get<PaginatedResponse<Task>>(`/projects/${projectId}/tasks`, {
            params: { per_page: 1000 },
        });
        return response.data;
    },

    get: async (projectId: string, taskId: string) => {
        const response = await api.get<Task>(`/projects/${projectId}/tasks/${taskId}`);
        return response.data;
    },

    create: async (projectId: string, data: TaskCreate) => {
        const response = await api.post<Task>(`/projects/${projectId}/tasks`, data);
        return response.data;
    },

    update: async (projectId: string, taskId: string, data: TaskUpdate) => {
        const response = await api.patch<Task>(`/projects/${projectId}/tasks/${taskId}`, data);
        return response.data;
    },

    delete: async (projectId: string, taskId: string) => {
        await api.delete(`/projects/${projectId}/tasks/${taskId}`);
    },

    indent: async (projectId: string, taskId: string) => {
        const response = await api.post<Task>(`/projects/${projectId}/tasks/${taskId}/indent`);
        return response.data;
    },

    outdent: async (projectId: string, taskId: string) => {
        const response = await api.post<Task>(`/projects/${projectId}/tasks/${taskId}/outdent`);
        return response.data;
    },

    reorder: async (projectId: string, taskId: string, data: TaskReorder) => {
        const response = await api.post<Task>(`/projects/${projectId}/tasks/${taskId}/reorder`, data);
        return response.data;
    },

    bulkCreate: async (projectId: string, data: TaskBulkCreate) => {
        const response = await api.post<TaskBulkCreateResponse>(`/projects/${projectId}/tasks/bulk`, data);
        return response.data;
    },

    bulkUpdate: async (projectId: string, data: TaskBulkUpdate) => {
        const response = await api.patch<BulkOperationResponse>(`/projects/${projectId}/tasks/bulk`, data);
        return response.data;
    },

    bulkDelete: async (projectId: string, data: TaskBulkDelete) => {
        const response = await api.delete<BulkOperationResponse>(`/projects/${projectId}/tasks/bulk`, { data });
        return response.data;
    },
};
