import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assignmentService } from "@/features/tasks/api/assignment.service";
import { taskKeys } from "@/features/tasks/hooks/useTasks";
import type { AssignmentCreate, AssignmentUpdate } from "@/features/tasks/types";

export const assignmentKeys = {
    all: ["assignments"] as const,
    lists: () => [...assignmentKeys.all, "list"] as const,
    list: (projectId: string, taskId: string) => [...assignmentKeys.lists(), projectId, taskId] as const,
};

export function useAssignments(projectId: string | undefined, taskId: string | undefined) {
    return useQuery({
        queryKey: assignmentKeys.list(projectId!, taskId!),
        queryFn: () => assignmentService.list(projectId!, taskId!),
        enabled: !!projectId && !!taskId,
    });
}

export function useCreateAssignment(projectId: string | undefined, taskId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: AssignmentCreate) => {
            if (!projectId || !taskId) throw new Error("No active project or task");
            return assignmentService.create(projectId, taskId, data);
        },
        onSuccess: () => {
            if (projectId && taskId) {
                queryClient.invalidateQueries({ queryKey: assignmentKeys.list(projectId, taskId) });
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useUpdateAssignment(projectId: string | undefined, taskId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ assignmentId, data }: { assignmentId: string; data: AssignmentUpdate }) => {
            if (!projectId || !taskId) throw new Error("No active project or task");
            return assignmentService.update(assignmentId, data);
        },
        onSuccess: () => {
            if (projectId && taskId) {
                queryClient.invalidateQueries({ queryKey: assignmentKeys.list(projectId, taskId) });
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useDeleteAssignment(projectId: string | undefined, taskId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (assignmentId: string) => {
            if (!projectId || !taskId) throw new Error("No active project or task");
            return assignmentService.delete(assignmentId);
        },
        onSuccess: () => {
            if (projectId && taskId) {
                queryClient.invalidateQueries({ queryKey: assignmentKeys.list(projectId, taskId) });
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}
