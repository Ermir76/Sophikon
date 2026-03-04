import { useMutation, useQueryClient } from "@tanstack/react-query";
import { scheduleService } from "@/features/gantt/api/schedule.service";
import { taskKeys } from "@/features/tasks/hooks/useTasks";

export function useCalculateSchedule(projectId?: string | null) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => {
            if (!projectId) throw new Error("No project ID provided");
            return scheduleService.calculate(projectId);
        },
        onSuccess: () => {
            if (projectId) {
                queryClient.invalidateQueries({
                    queryKey: taskKeys.list(projectId),
                });
            }
        },
    });
}
