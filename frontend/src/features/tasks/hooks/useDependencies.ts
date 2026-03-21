import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dependencyService } from "@/features/tasks/api/dependency.service";
import type { DependencyCreate, DependencyUpdate } from "@/features/tasks/types";
import { taskKeys } from "./useTasks";

export const dependencyKeys = {
    all: ["tasks", "dependencies"] as const,
    lists: () => [...dependencyKeys.all, "list"] as const,
    list: (projectId: string) => [...dependencyKeys.lists(), projectId] as const,
};

export function useDependencies(projectId: string | undefined) {
    return useQuery({
        queryKey: dependencyKeys.list(projectId!),
        queryFn: () => dependencyService.list(projectId!),
        enabled: !!projectId,
    });
}

export function useCreateDependency(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: DependencyCreate) => {
            if (!projectId) throw new Error("No active project");
            return dependencyService.create(projectId, data);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: dependencyKeys.list(projectId) });
                // Also invalidate tasks since dependencies might affect dates via scheduling
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useUpdateDependency(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ dependencyId, data }: { dependencyId: string; data: DependencyUpdate }) => {
            if (!projectId) throw new Error("No active project");
            return dependencyService.update(projectId, dependencyId, data);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: dependencyKeys.list(projectId) });
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useDeleteDependency(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (dependencyId: string) => {
            if (!projectId) throw new Error("No active project");
            return dependencyService.delete(projectId, dependencyId);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: dependencyKeys.list(projectId) });
                // Also invalidate tasks since dependencies affect dates
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}
