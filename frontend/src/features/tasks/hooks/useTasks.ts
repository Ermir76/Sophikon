import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { taskService } from "@/features/tasks/api/task.service";
import type {
    TaskCreate,
    TaskUpdate,
    TaskReorder,
    TaskBulkCreate,
    TaskBulkUpdate,
    TaskBulkDelete
} from "@/features/tasks/types";

export const taskKeys = {
    all: ["tasks"] as const,
    lists: () => [...taskKeys.all, "list"] as const,
    list: (projectId: string) => [...taskKeys.lists(), projectId] as const,
    details: () => [...taskKeys.all, "detail"] as const,
    detail: (projectId: string, taskId: string) => [...taskKeys.details(), projectId, taskId] as const,
};

export function useTasks(projectId: string | undefined) {
    return useQuery({
        queryKey: taskKeys.list(projectId!),
        queryFn: () => taskService.list(projectId!),
        enabled: !!projectId,
    });
}

export function useTask(projectId: string | undefined, taskId: string | undefined) {
    return useQuery({
        queryKey: taskKeys.detail(projectId!, taskId!),
        queryFn: () => taskService.get(projectId!, taskId!),
        enabled: !!projectId && !!taskId,
    });
}

export function useCreateTask(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: TaskCreate) => {
            if (!projectId) throw new Error("No active project");
            return taskService.create(projectId, data);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useUpdateTask(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ taskId, data }: { taskId: string; data: TaskUpdate }) => {
            if (!projectId) throw new Error("No active project");
            return taskService.update(projectId, taskId, data);
        },
        onSuccess: (_, variables) => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.detail(projectId, variables.taskId) });
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useDeleteTask(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (taskId: string) => {
            if (!projectId) throw new Error("No active project");
            return taskService.delete(projectId, taskId);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useIndentTask(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (taskId: string) => {
            if (!projectId) throw new Error("No active project");
            return taskService.indent(projectId, taskId);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useOutdentTask(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (taskId: string) => {
            if (!projectId) throw new Error("No active project");
            return taskService.outdent(projectId, taskId);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useReorderTask(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ taskId, data }: { taskId: string; data: TaskReorder }) => {
            if (!projectId) throw new Error("No active project");
            return taskService.reorder(projectId, taskId, data);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

// Bulk Hooks
export function useBulkCreateTasks(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: TaskBulkCreate) => {
            if (!projectId) throw new Error("No active project");
            return taskService.bulkCreate(projectId, data);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useBulkUpdateTasks(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: TaskBulkUpdate) => {
            if (!projectId) throw new Error("No active project");
            return taskService.bulkUpdate(projectId, data);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}

export function useBulkDeleteTasks(projectId: string | undefined) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: TaskBulkDelete) => {
            if (!projectId) throw new Error("No active project");
            return taskService.bulkDelete(projectId, data);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
        },
    });
}
