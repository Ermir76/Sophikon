import { api } from "@/shared/api/api";
import type { TaskAttachment } from "@/features/tasks/types";

export const attachmentService = {
  list: async (projectId: string, taskId: string) => {
    const response = await api.get<TaskAttachment[]>(
      `/projects/${projectId}/tasks/${taskId}/attachments`,
    );
    return response.data;
  },

  upload: async (
    projectId: string,
    taskId: string,
    payload: { file: File; description?: string },
  ) => {
    const formData = new FormData();
    formData.append("file", payload.file);
    if (payload.description) {
      formData.append("description", payload.description);
    }
    const response = await api.post<TaskAttachment>(
      `/projects/${projectId}/tasks/${taskId}/attachments`,
      formData,
    );
    return response.data;
  },

  remove: async (projectId: string, taskId: string, attachmentId: string) => {
    await api.delete(
      `/projects/${projectId}/tasks/${taskId}/attachments/${attachmentId}`,
    );
  },
};
