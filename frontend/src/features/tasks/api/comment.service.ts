import { api } from "@/shared/api/api";
import type {
    CommentEntityType,
    TaskComment,
    TaskCommentCreate,
    TaskCommentListResponse,
    TaskCommentUpdate,
} from "@/features/tasks/types";

export const commentService = {
    async list(entityType: CommentEntityType, entityId: string) {
        const response = await api.get<TaskCommentListResponse>(
            `/comments/entity/${entityType}/${entityId}`,
        );
        return response.data;
    },

    async create(payload: TaskCommentCreate) {
        const response = await api.post<TaskComment>("/comments", payload);
        return response.data;
    },

    async update(commentId: string, payload: TaskCommentUpdate) {
        const response = await api.patch<TaskComment>(`/comments/${commentId}`, payload);
        return response.data;
    },

    async delete(commentId: string) {
        await api.delete(`/comments/${commentId}`);
    },
};
