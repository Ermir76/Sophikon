import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { resourceService } from "@/features/resources/api/resource.service";
import type { ResourceCreate, ResourceUpdate } from "@/features/resources/types";

export const resourceKeys = {
    all: ["resources"] as const,
    lists: () => [...resourceKeys.all, "list"] as const,
    list: (projectId: string) => [...resourceKeys.lists(), projectId] as const,
    details: () => [...resourceKeys.all, "detail"] as const,
    detail: (projectId: string, resourceId: string) => [...resourceKeys.details(), projectId, resourceId] as const,
};

export function useResources(projectId: string | undefined) {
    return useQuery({
        queryKey: resourceKeys.list(projectId!),
        queryFn: () => resourceService.list(projectId!),
        enabled: !!projectId,
    });
}

export function useResource(projectId: string | undefined, resourceId: string | undefined) {
    return useQuery({
        queryKey: resourceKeys.detail(projectId!, resourceId!),
        queryFn: () => resourceService.get(projectId!, resourceId!),
        enabled: !!projectId && !!resourceId,
    });
}

export function useCreateResource(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: ResourceCreate) => {
            if (!projectId) throw new Error("No active project");
            return resourceService.create(projectId, data);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: resourceKeys.list(projectId) });
            }
        },
    });
}

export function useUpdateResource(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ resourceId, data }: { resourceId: string; data: ResourceUpdate }) => {
            if (!projectId) throw new Error("No active project");
            return resourceService.update(projectId, resourceId, data);
        },
        onSuccess: (_, variables) => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: resourceKeys.detail(projectId, variables.resourceId) });
                queryClient.invalidateQueries({ queryKey: resourceKeys.list(projectId) });
            }
        },
    });
}

export function useDeleteResource(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (resourceId: string) => {
            if (!projectId) throw new Error("No active project");
            return resourceService.delete(projectId, resourceId);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: resourceKeys.list(projectId) });
            }
        },
    });
}

/**
 * INTENTIONAL ARCHITECTURE EXCEPTION:
 * Bulk delete is intentionally client-emulated via `Promise.allSettled` over single delete calls.
 * This is an accepted constraint due to the current backend not supporting a native bulk-delete endpoint
 * for resources, and the feature only requiring very small delete batches.
 * Do not flag this as accidental architectural drift during consistency audits.
 */
export function useBulkDeleteResources(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (resourceIds: string[]) => {
            if (!projectId) throw new Error("No active project");

            const results = await Promise.allSettled(
                resourceIds.map((id) => resourceService.delete(projectId, id))
            );

            const succeeded = results.filter((r) => r.status === "fulfilled").length;
            const failed = results.filter((r) => r.status === "rejected").length;

            return { succeeded, failed };
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: resourceKeys.list(projectId) });
            }
        },
    });
}
