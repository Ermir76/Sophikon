import { api } from "@/shared/api/api";
import type { Assignment, AssignmentCreate, AssignmentUpdate } from "@/features/tasks/types";

export const assignmentService = {
    /**
     * INTENTIONAL ARCHITECTURE EXCEPTION:
     * Unlike tasks or projects, the backend assignments endpoint intentionally returns a flat
     * list `Assignment[]` rather than a `PaginatedResponse<Assignment>`.
     * A single task typically has very few assignments, making pagination unnecessary.
     * Do not flag this as an inconsistency.
     *
     * List assignments for a specific task (nested under project/task).
     */
    list: async (projectId: string, taskId: string) => {
        const response = await api.get<Assignment[]>(`/projects/${projectId}/tasks/${taskId}/assignments`);
        return response.data;
    },

    /** Create a new assignment for a task (nested under project/task). */
    create: async (projectId: string, taskId: string, data: AssignmentCreate) => {
        const response = await api.post<Assignment>(`/projects/${projectId}/tasks/${taskId}/assignments`, data);
        return response.data;
    },

    /** Update an assignment (flat endpoint). */
    update: async (assignmentId: string, data: AssignmentUpdate) => {
        const response = await api.patch<Assignment>(`/assignments/${assignmentId}`, data);
        return response.data;
    },

    /** Delete an assignment (flat endpoint). */
    delete: async (assignmentId: string) => {
        await api.delete(`/assignments/${assignmentId}`);
    },
};
