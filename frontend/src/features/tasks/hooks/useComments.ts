import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { commentService } from "@/features/tasks/api/comment.service";
import { taskKeys } from "@/features/tasks/hooks/useTasks";
import type { CommentEntityType, TaskCommentCreate, TaskCommentUpdate } from "@/features/tasks/types";

export const commentKeys = {
    all: ["comments"] as const,
    byEntity: (entityType: CommentEntityType, entityId: string) =>
        [...commentKeys.all, entityType, entityId] as const,
};

export function useComments(entityType: CommentEntityType, entityId: string | undefined) {
    return useQuery({
        queryKey: entityId ? commentKeys.byEntity(entityType, entityId) : commentKeys.all,
        queryFn: () => commentService.list(entityType, entityId!),
        enabled: Boolean(entityId),
    });
}

export function useCreateComment(
    projectId: string | undefined,
    entityType: CommentEntityType,
    entityId: string | undefined,
) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: Omit<TaskCommentCreate, "entity_type" | "entity_id">) => {
            if (!entityId) {
                throw new Error("No active entity");
            }
            return commentService.create({
                entity_type: entityType,
                entity_id: entityId,
                content: payload.content,
                parent_comment_id: payload.parent_comment_id ?? null,
            });
        },
        onSuccess: () => {
            if (!entityId) {
                return;
            }
            queryClient.invalidateQueries({ queryKey: commentKeys.byEntity(entityType, entityId) });
            if (projectId && entityType === "task") {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
                queryClient.invalidateQueries({ queryKey: taskKeys.detail(projectId, entityId) });
            }
        },
    });
}

export function useUpdateComment(
    projectId: string | undefined,
    entityType: CommentEntityType,
    entityId: string | undefined,
) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ commentId, data }: { commentId: string; data: TaskCommentUpdate }) =>
            commentService.update(commentId, data),
        onSuccess: () => {
            if (!entityId) {
                return;
            }
            queryClient.invalidateQueries({ queryKey: commentKeys.byEntity(entityType, entityId) });
            if (projectId && entityType === "task") {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
                queryClient.invalidateQueries({ queryKey: taskKeys.detail(projectId, entityId) });
            }
        },
    });
}

export function useDeleteComment(
    projectId: string | undefined,
    entityType: CommentEntityType,
    entityId: string | undefined,
) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (commentId: string) => commentService.delete(commentId),
        onSuccess: () => {
            if (!entityId) {
                return;
            }
            queryClient.invalidateQueries({ queryKey: commentKeys.byEntity(entityType, entityId) });
            if (projectId && entityType === "task") {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
                queryClient.invalidateQueries({ queryKey: taskKeys.detail(projectId, entityId) });
            }
        },
    });
}
