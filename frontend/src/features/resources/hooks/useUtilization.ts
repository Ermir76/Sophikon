import { useQuery } from "@tanstack/react-query";
import { utilizationService } from "@/features/resources/api/utilization.service";

export const utilizationKeys = {
    all: ["utilization"] as const,
    project: (projectId: string, startDate: string, endDate: string) =>
        [...utilizationKeys.all, "project", projectId, startDate, endDate] as const,
    resource: (projectId: string, resourceId: string, startDate: string, endDate: string) =>
        [...utilizationKeys.all, "resource", projectId, resourceId, startDate, endDate] as const,
    overAllocations: (projectId: string, startDate: string, endDate: string) =>
        [...utilizationKeys.all, "over-allocations", projectId, startDate, endDate] as const,
};

export function useProjectUtilization(
    projectId: string | undefined,
    startDate: string | undefined,
    endDate: string | undefined,
) {
    return useQuery({
        queryKey: utilizationKeys.project(projectId!, startDate!, endDate!),
        queryFn: () => utilizationService.getProjectUtilization(projectId!, startDate!, endDate!),
        enabled: !!projectId && !!startDate && !!endDate,
    });
}

export function useResourceUtilization(
    projectId: string | undefined,
    resourceId: string | undefined,
    startDate: string | undefined,
    endDate: string | undefined,
) {
    return useQuery({
        queryKey: utilizationKeys.resource(projectId!, resourceId!, startDate!, endDate!),
        queryFn: () => utilizationService.getResourceUtilization(projectId!, resourceId!, startDate!, endDate!),
        enabled: !!projectId && !!resourceId && !!startDate && !!endDate,
    });
}

export function useOverAllocations(
    projectId: string | undefined,
    startDate: string | undefined,
    endDate: string | undefined,
) {
    return useQuery({
        queryKey: utilizationKeys.overAllocations(projectId!, startDate!, endDate!),
        queryFn: () => utilizationService.getOverAllocations(projectId!, startDate!, endDate!),
        enabled: !!projectId && !!startDate && !!endDate,
    });
}
